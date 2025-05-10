import logging
from datetime import datetime, timedelta
from app import db
from app.models import Product, Market, Price, Region
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.batch_size = 50  # Process records in batches for better performance

    def process_and_save(self, raw_data: List[Dict]) -> int:
        """
        Process scraped data and save to database in batches
        
        Args:
            raw_data: List of dictionaries containing scraped price data
            
        Returns:
            int: Number of successfully saved records
        """
        if not raw_data:
            logger.warning("No data provided to processor")
            return 0

        saved_count = 0
        batch = []
        
        for record in raw_data:
            try:
                processed = self._process_single_record(record)
                if processed:
                    batch.append(processed)
                    
                    # Commit in batches
                    if len(batch) >= self.batch_size:
                        saved_count += self._save_batch(batch)
                        batch = []
                        
            except Exception as e:
                logger.error(f"Failed to process record: {str(e)}", exc_info=True)
                continue
                
        # Save any remaining records in the batch
        if batch:
            saved_count += self._save_batch(batch)
            
        logger.info(f"Successfully processed and saved {saved_count} records")
        return saved_count

    def _process_single_record(self, record: Dict) -> Optional[Dict]:
        """Process a single raw data record into database-ready format"""
        if not self._validate_record(record):
            return None

        try:
            # Standardize field names
            processed = {
                'commodity': record.get('commodity', record.get('product', 'Unknown')),
                'market': record.get('market', 'Unknown'),
                'wholesale_price': self._parse_price(record.get('wholesale_price')),
                'retail_price': self._parse_price(record.get('retail_price')),
                'unit': record.get('unit', 'kg').lower(),
                'date': self._parse_date(record.get('date')),
                'region': record.get('region'),
                'latitude': record.get('latitude'),
                'longitude': record.get('longitude'),
                'source': record.get('source', 'AMIS Kenya')
            }
            
            # Ensure we have at least one valid price
            if processed['wholesale_price'] is None and processed['retail_price'] is None:
                logger.warning(f"Record has no valid prices: {record}")
                return None
                
            return processed
            
        except Exception as e:
            logger.error(f"Record processing failed: {str(e)}")
            return None

    def _save_batch(self, batch: List[Dict]) -> int:
        """Save a batch of processed records to database"""
        saved_in_batch = 0
        
        try:
            for record in batch:
                # Get or create Market with Region
                market = self._get_or_create_market({
                    'name': record['market'],
                    'region': record['region'],
                    'latitude': record['latitude'],
                    'longitude': record['longitude']
                })
                
                # Get or create Product
                product = self._get_or_create_product({
                    'name': record['commodity'],
                    'unit': record['unit']
                })
                
                # Create Price entry
                price = Price(
                    product_id=product.id,
                    market_id=market.id,
                    wholesale_price=record['wholesale_price'],
                    retail_price=record['retail_price'],
                    unit=record['unit'],
                    date=record['date'],
                    source=record['source'],
                    scraped_at=datetime.now()
                )
                
                db.session.add(price)
                saved_in_batch += 1
                
            db.session.commit()
            return saved_in_batch
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Batch save failed: {str(e)}", exc_info=True)
            return 0

    def _get_or_create_market(self, market_data: Dict) -> Market:
        """Get or create Market and associated Region"""
        # Handle Region first
        region = None
        if market_data.get('region'):
            region = Region.query.filter_by(name=market_data['region']).first()
            if not region:
                region = Region(name=market_data['region'])
                db.session.add(region)
                db.session.flush()  # Get the ID before committing
                
        # Then handle Market
        market = Market.query.filter_by(name=market_data['name']).first()
        if not market:
            market = Market(
                name=market_data['name'],
                region=region,
                latitude=market_data.get('latitude'),
                longitude=market_data.get('longitude')
            )
            db.session.add(market)
            db.session.flush()
            
        return market

    def _get_or_create_product(self, product_data: Dict) -> Product:
        """Get or create Product"""
        product = Product.query.filter_by(name=product_data['name']).first()
        if not product:
            product = Product(
                name=product_data['name'],
                category='Agricultural',  # Default category
                unit=product_data.get('unit', 'kg')
            )
            db.session.add(product)
            db.session.flush()
            
        return product

    def _validate_record(self, record: Dict) -> bool:
        """Validate that a record has required fields"""
        required = ['commodity', 'market']
        return all(field in record for field in required)

    def _parse_price(self, price) -> Optional[float]:
        """Convert price string to float, handling various formats"""
        if price is None:
            return None
            
        try:
            if isinstance(price, (int, float)):
                return float(price)
                
            # Remove currency symbols and thousands separators
            cleaned = ''.join(c for c in str(price) if c.isdigit() or c == '.')
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    def _parse_date(self, date_str) -> datetime.date:
        """Parse date from various string formats"""
        if date_str is None:
            return datetime.now().date()
            
        try:
            # Try common date formats
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%b %d, %Y'):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
                    
            # Fallback to current date if parsing fails
            return datetime.now().date()
        except Exception:
            return datetime.now().date()

    def clean_old_data(self, days: int = 30) -> int:
        """
        Remove price data older than specified number of days
        
        Args:
            days: Number of days to keep
            
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Count before deletion
            count_before = Price.query.count()
            
            # Delete records
            Price.query.filter(Price.date < cutoff_date).delete()
            db.session.commit()
            
            count_after = Price.query.count()
            return count_before - count_after
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Data cleaning failed: {str(e)}", exc_info=True)
            return 0
import json
from datetime import datetime
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
from kafka import KafkaProducer
from kafka.errors import KafkaError


class KafkaPipeline:
    def __init__(self, kafka_servers, kafka_topic):
        self.kafka_topic = kafka_topic

        # Kafka Producer 초기화
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=kafka_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                acks='all',
                max_in_flight_requests_per_connection=1,
            )
        except Exception as e:
            raise Exception(f"Kafka Producer 초기화 실패: {e}")

        self.stats = {
            'processed': 0,
            'kafka_sent': 0,
            'kafka_failed': 0
        }

    @classmethod
    def from_crawler(cls, crawler):
        kafka_servers = crawler.settings.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        kafka_topic = crawler.settings.get('KAFKA_TOPIC', 'recall-notice-urls')

        return cls(
            kafka_servers=kafka_servers,
            kafka_topic=kafka_topic
        )

    def process_item(self, item, spider):
        self.stats['processed'] += 1
        adapter = ItemAdapter(item)
        url = adapter.get('url')

        if not url:
            raise DropItem(f"Missing URL in item: {item}")

        # Kafka로 전송
        try:
            message = dict(adapter)
            message['crawled_at'] = datetime.now().isoformat()

            # Kafka에 메시지 전송
            future = self.kafka_producer.send(
                self.kafka_topic,
                key=url,
                value=message
            )

            # 전송 완료 대기
            record_metadata = future.get(timeout=10)

            spider.logger.info(
                f"Kafka 전송 성공 - Topic: {record_metadata.topic}, "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}, "
                f"URL: {url}"
            )

            self.stats['kafka_sent'] += 1
            return item

        except KafkaError as e:
            self.stats['kafka_failed'] += 1
            spider.logger.error(f"Kafka 전송 실패 (URL: {url}): {e}")
            raise DropItem(f"Kafka send failed: {e}")

        except Exception as e:
            self.stats['kafka_failed'] += 1
            spider.logger.error(f"처리 중 오류 발생 (URL: {url}): {e}", exc_info=True)
            raise DropItem(f"Processing error: {e}")

    def close_spider(self, spider):
        # 통계 출력
        spider.logger.info("=" * 50)
        spider.logger.info("크롤링 통계:")
        spider.logger.info(f"  처리된 아이템: {self.stats['processed']}")
        spider.logger.info(f"  Kafka 전송 성공: {self.stats['kafka_sent']}")
        spider.logger.info(f"  Kafka 전송 실패: {self.stats['kafka_failed']}")
        spider.logger.info("=" * 50)

        # Kafka Producer 종료
        if hasattr(self, 'kafka_producer'):
            try:
                self.kafka_producer.flush(timeout=10)
                self.kafka_producer.close()
                spider.logger.info("Kafka Producer 종료 완료")
            except Exception as e:
                spider.logger.error(f"Kafka Producer 종료 중 오류: {e}")

"""
Kafka 설정 및 토픽 생성 예시 스크립트
실제 Kafka 서버에서 실행하거나, Kafka 관리 도구를 사용하여 토픽을 생성하세요.
"""
import yaml
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError


def create_kafka_topics(config_path: str = 'config/config.yaml'):
    """
    설정 파일에서 Kafka 토픽 목록을 읽어서 생성
    
    주의: 이 스크립트는 Kafka 서버에 직접 접근할 수 있는 환경에서 실행해야 합니다.
    """
    # 설정 로드
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    kafka_config = config['kafka']
    bootstrap_servers = kafka_config['bootstrap_servers']
    topics = kafka_config['topics']
    
    # AdminClient 생성
    admin_client = KafkaAdminClient(
        bootstrap_servers=bootstrap_servers,
        client_id='recall_pipeline_setup'
    )
    
    # 토픽 생성
    topic_list = []
    for topic_name, topic_value in topics.items():
        topic_list.append(
            NewTopic(
                name=topic_value,
                num_partitions=3,  # 파티션 수 (필요에 따라 조정)
                replication_factor=1  # 리플리케이션 팩터 (단일 브로커면 1)
            )
        )
        print(f"토픽 생성 예정: {topic_value}")
    
    try:
        # 토픽 생성
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print("모든 토픽이 성공적으로 생성되었습니다.")
    except TopicAlreadyExistsError as e:
        print(f"일부 토픽이 이미 존재합니다: {e}")
    except Exception as e:
        print(f"토픽 생성 중 오류 발생: {e}")
    finally:
        admin_client.close()


if __name__ == '__main__':
    print("Kafka 토픽 생성 스크립트")
    print("=" * 50)
    create_kafka_topics()


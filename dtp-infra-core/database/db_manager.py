import boto3
import json
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session


# Global Pool
_ENGINE = None
_SESSION_FACTORY = None

def get_secret(secret_name, region_name="us-east-1"):
    """
    Retrieves database credentials from AWS Secrets Manager.
    """
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    return json.loads(get_secret_value_response['SecretString'])

def init_db_engine(env="production"):
    global _ENGINE, _SESSION_FACTORY
    
    secret_name = f"dtp/database/{env}/credentials"
    creds = get_secret(secret_name)
    
    # OPTIMIZATION: Use the RDS Proxy Endpoint if available in Env, else Host
    db_host = os.getenv("DB_PROXY_ENDPOINT", creds['host'])
    
    db_url = f"postgresql://{creds['username']}:{creds['password']}@{db_host}:{creds['port']}/dtp_core"

    # OPTIMIZATION: Disable client-side pooling if using RDS Proxy
    # RDS Proxy handles pooling; client side should be lightweight.
    _ENGINE = create_engine(
        db_url,
        pool_size=5,            # Reduced size (Proxy handles the heavy lifting)
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
        isolation_level="READ COMMITTED" # Required for proper Proxy behavior
    )

    # RLS Hook (Security)
    @event.listens_for(_ENGINE, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        cursor = dbapi_connection.cursor()
        # Security: Reset context to prevent data leak between requests
        cursor.execute("RESET app.current_tenant") 
        cursor.close()

    _SESSION_FACTORY = scoped_session(sessionmaker(bind=_ENGINE))
    return _ENGINE

def get_tenant_session(tenant_id: str):
    """
    Returns a DB Session scoped to a specific tenant.
    """
    if not _ENGINE:
        init_db_engine()
        
    session = _SESSION_FACTORY()
    
    # Enforce RLS for this specific session
    session.execute(f"SELECT set_tenant_context('{tenant_id}')")
    return session
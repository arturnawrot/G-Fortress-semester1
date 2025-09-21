from neontology import init_neontology, auto_constrain_neo4j
from security.hashing import get_password_hash
from config import settings
from db.models import AuthUser

def connect_to_db():
    init_neontology(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
    )

def setup_database():
    admin_user = AuthUser.match("admin")

    if admin_user:
        print("User 'admin' exists.")
        return

    try:
        auto_constrain_neo4j()
    except Exception as e:
        print(f"An error occurred while applying constraints: {e}")
    
    print("Seeding default admin user")
    
    hashed_admin_password = get_password_hash(settings.DEFAULT_ADMIN_LOGIN)

    admin_user_to_seed = AuthUser(
        username=settings.DEFAULT_ADMIN_PASSWORD,
        hashed_password=hashed_admin_password
    )
    
    admin_user_to_seed.merge()
    
    print("Default admin user (admin/admin) has been ensured in the database.")

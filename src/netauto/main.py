from netauto.composition import create_runtime_application
from netauto.config import get_database_url

runtime = create_runtime_application(get_database_url())
engine = runtime.engine
app = runtime.app

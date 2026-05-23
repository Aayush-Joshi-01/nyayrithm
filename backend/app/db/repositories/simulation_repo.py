from __future__ import annotations

from app.db.adapters.postgres import PostgresRepository
from app.db.adapters.mongodb import MongoRepository
from app.models.simulation import Simulation


class SimulationPostgresRepository(PostgresRepository[Simulation]):
    table_name = "simulations"
    model_cls = Simulation


class SimulationMongoRepository(MongoRepository[Simulation]):
    collection_name = "simulations"
    model_cls = Simulation

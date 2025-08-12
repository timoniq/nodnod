import pytest
import asyncio
import fntypes
from nodnod import Node, Scope, EventLoopAgent, scalar_node, Value


class TestInjection:
    @pytest.mark.asyncio
    async def test_injection_basic(self):
        class Database:
            def query(self) -> str:
                return "result from db"
        
        @scalar_node
        class Service:
            @classmethod
            def __compose__(cls, db: Database) -> str:
                return f"Service used: {db.query()}"
        
        agent = EventLoopAgent.build({Service})
        scope = Scope(detail="test")
        
        # Inject the database dependency
        scope.push(Value(Database, Database()))
        
        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(Service)
            assert fntypes.is_some(result)
            assert result.unwrap().value == "Service used: result from db"
    
    @pytest.mark.asyncio
    async def test_multiple_injections(self):
        class Config:
            def __init__(self, setting: str):
                self.setting = setting
        
        class Logger:
            def log(self, msg: str) -> str:
                return f"LOG: {msg}"
        
        @scalar_node
        class Application:
            @classmethod
            def __compose__(cls, config: Config, logger: Logger) -> str:
                message = f"App started with {config.setting}"
                return logger.log(message)
        
        agent = EventLoopAgent.build({Application})
        scope = Scope(detail="test")
        
        # Inject multiple dependencies
        scope.push(Value(Config, Config("production")))
        scope.push(Value(Logger, Logger()))
        
        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(Application)
            assert fntypes.is_some(result)
            assert result.unwrap().value == "LOG: App started with production"
    
    @pytest.mark.asyncio
    async def test_scoped_injection(self):
        class DatabaseConnection:
            def __init__(self, name: str):
                self.name = name
        
        @scalar_node
        class UserService:
            @classmethod
            def __compose__(cls, db: DatabaseConnection) -> str:
                return f"Users from {db.name}"
        
        @scalar_node
        class AdminService:
            @classmethod
            def __compose__(cls, db: DatabaseConnection) -> str:
                return f"Admins from {db.name}"
        
        agent = EventLoopAgent.build({UserService, AdminService})
        
        # Create different scopes with different database connections
        global_scope = Scope(detail="global")
        user_scope = global_scope.create_child("user")
        admin_scope = global_scope.create_child("admin")
        
        user_scope.push(Value(DatabaseConnection, DatabaseConnection("user_db")))
        admin_scope.push(Value(DatabaseConnection, DatabaseConnection("admin_db")))
        
        async with user_scope:
            await agent.run(
                local_scope=user_scope, 
                mapped_scopes={AdminService: admin_scope}
            )
            
            user_result = user_scope.retrieve(UserService)
            admin_result = admin_scope.retrieve(AdminService)
            
            assert fntypes.is_some(user_result)
            assert fntypes.is_some(admin_result)
            
            assert user_result.unwrap().value == "Users from user_db"
            # AdminService should use user_db since it inherits from user_scope
            assert admin_result.unwrap().value == "Admins from user_db"
        
        await admin_scope.close()
        await global_scope.close()
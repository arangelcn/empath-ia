// MongoDB Initialization Script for EmpatIA
// This script runs once when MongoDB starts

print('🚀 Iniciando configuração do banco EmpatIA...');

// Switch to admin database to create user
db = db.getSiblingDB('admin');

// Create application user with read/write access
print('👤 Criando usuário da aplicação...');
try {
    db.createUser({
        user: 'empatia_user',
        pwd: 'empatia_pass',
        roles: [
            { role: 'readWrite', db: 'empatia_db' },
            { role: 'dbOwner', db: 'empatia_db' }
        ]
    });
    print('✅ Usuário empatia_user criado com sucesso');
} catch (error) {
    if (error.code === 11000) {
        print('⚠️  Usuário empatia_user já existe');
    } else {
        print('❌ Erro ao criar usuário:', error.message);
    }
}

// Switch to application database
db = db.getSiblingDB('empatia_db');

// Create collections with validation
print('📂 Criando coleções...');

// Conversations collection
try {
    db.createCollection('conversations', {
        validator: {
            $jsonSchema: {
                bsonType: "object",
                required: ["chat_id", "session_id", "created_at", "is_active"],
                properties: {
                    chat_id: { bsonType: "string" },
                    session_id: { bsonType: "string" },
                    legacy_session_id: { bsonType: "string" },
                    therapeutic_session_id: { bsonType: "string" },
                    username: { bsonType: "string" },
                    created_at: { bsonType: "date" },
                    updated_at: { bsonType: "date" },
                    is_active: { bsonType: "bool" },
                    title: { bsonType: "string" },
                    metadata: { bsonType: "object" }
                }
            }
        }
    });
    print('✅ Coleção conversations criada');
} catch (error) {
    print('⚠️  Coleção conversations já existe ou erro:', error.message);
}

// Messages collection
try {
    db.createCollection('messages', {
        validator: {
            $jsonSchema: {
                bsonType: "object",
                required: ["session_id", "content"],
                properties: {
                    chat_id: { bsonType: "string" },
                    session_id: { bsonType: "string" },
                    therapeutic_session_id: { bsonType: "string" },
                    username: { bsonType: "string" },
                    message_type: { bsonType: "string", enum: ["user", "ai"] },
                    type: { bsonType: "string", enum: ["user", "ai"] },
                    content: { bsonType: "string" },
                    timestamp: { bsonType: "date" },
                    emotion_data: { bsonType: "object" },
                    metadata: { bsonType: "object" }
                }
            }
        }
    });
    print('✅ Coleção messages criada');
} catch (error) {
    print('⚠️  Coleção messages já existe ou erro:', error.message);
}

// Create indexes for performance
print('🔍 Criando índices...');

// Conversations indexes
db.conversations.createIndex({ "chat_id": 1 }, { unique: true, sparse: true });
db.conversations.createIndex({ "session_id": 1 });
db.conversations.createIndex({ "legacy_session_id": 1 });
db.conversations.createIndex(
    { "username": 1, "therapeutic_session_id": 1 },
    {
        unique: true,
        partialFilterExpression: {
            username: { $type: "string" },
            therapeutic_session_id: { $type: "string" }
        }
    }
);
db.conversations.createIndex({ "created_at": -1 });
db.conversations.createIndex({ "is_active": 1 });
db.conversations.createIndex({ "updated_at": -1 });

// Messages indexes
db.messages.createIndex({ "chat_id": 1 });
db.messages.createIndex({ "session_id": 1 });
db.messages.createIndex({ "username": 1, "therapeutic_session_id": 1 });
db.messages.createIndex({ "timestamp": -1 });
db.messages.createIndex({ "message_type": 1 });
db.messages.createIndex({ 
    "session_id": 1, 
    "timestamp": -1 
});

print('✅ Índices criados com sucesso');

// Insert sample data
print('📝 Inserindo dados de exemplo...');

// Sample conversation
const sampleSessionId = 'demo-session-' + new Date().getTime();
const sampleChatId = 'chat_demo_' + new Date().getTime();

try {
    db.conversations.insertOne({
        chat_id: sampleChatId,
        session_id: sampleSessionId,
        legacy_session_id: sampleSessionId,
        therapeutic_session_id: 'session-1',
        username: 'demo',
        title: 'Conversa de Demonstração',
        created_at: new Date(),
        updated_at: new Date(),
        is_active: true,
        metadata: {
            user_agent: 'Mozilla/5.0 (Demo)',
            ip_address: '127.0.0.1'
        }
    });
    
    // Sample messages
    db.messages.insertMany([
        {
            chat_id: sampleChatId,
            session_id: sampleSessionId,
            therapeutic_session_id: 'session-1',
            username: 'demo',
            type: 'user',
            message_type: 'user',
            content: 'Olá! Como você pode me ajudar?',
            timestamp: new Date(Date.now() - 10000),
            metadata: {}
        },
        {
            chat_id: sampleChatId,
            session_id: sampleSessionId,
            therapeutic_session_id: 'session-1',
            username: 'demo',
            type: 'ai',
            message_type: 'ai',
            content: 'Olá! Sou a EmpatIA, sua assistente de inteligência artificial com análise emocional. Posso te ajudar com conversas empáticas e análise de sentimentos. Como posso ajudá-lo hoje?',
            timestamp: new Date(),
            emotion_data: {
                sentiment: 'positive',
                confidence: 0.95,
                emotions: {
                    joy: 0.8,
                    empathy: 0.9
                }
            },
            metadata: {
                model: 'gpt-3.5-turbo',
                response_time: 1.2
            }
        }
    ]);
    
    print('✅ Dados de exemplo inseridos');
} catch (error) {
    print('❌ Erro ao inserir dados de exemplo:', error.message);
}

// Verify setup
print('🔍 Verificando configuração...');
print('📊 Collections:', db.getCollectionNames());
print('📈 Conversations count:', db.conversations.countDocuments());
print('💬 Messages count:', db.messages.countDocuments());

print('🎉 Banco EmpatIA configurado com sucesso!');
print('🌐 Acesse http://localhost:8081 para MongoDB Express');
print('💡 Use: mongo empatia_db --eval "db.conversations.find()" para verificar'); 

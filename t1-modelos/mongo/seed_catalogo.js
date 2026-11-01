// ==============================================================================
// Seed MongoDB - Catálogo Flexível da Loja Horizonte
// Disciplina: Persistência de Dados e Bancos Distribuídos - Trabalho 1 (T1)
// ==============================================================================

db = db.getSiblingDB("horizonte_catalogo");

// Criar índices para busca eficiente
db.produtos.createIndex({ "produto_id": 1 }, { unique: true });
db.produtos.createIndex({ "categoria": 1 });
db.produtos.createIndex({ "lojista_id": 1 });

// Limpar antes de popular
db.produtos.deleteMany({});

// Inserção de produtos com atributos dinâmicos e heterogêneos por categoria técnica
db.produtos.insertMany([
  {
    produto_id: 10,
    lojista_id: 101,
    nome: "Mochila de Trilha 25L Impermeável",
    categoria: "Mochilas e Bagagens",
    marca: "Horizonte Trekker",
    schema_version: 2,
    atributos: {
      capacidade_l: 25,
      compartimento_notebook: true,
      peso_gramas: 850,
      material: "Cordura Ripstop",
      cor: "Verde Musgo"
    },
    tags: ["trilha", "camping", "caminhada", "outdoor"],
    data_atualizacao: new Date()
  },
  {
    produto_id: 11,
    lojista_id: 101,
    nome: "Bota Impermeável para Caminhada e Trekking",
    categoria: "Calçados Esportivos",
    marca: "Trekking Pro",
    schema_version: 2,
    atributos: {
      tamanho: 41,
      tipo_solado: "Vibram Antiderrapante",
      impermeavel: true,
      genero: "Unissex"
    },
    tags: ["bota", "caminhada", "trilha", "impermeavel"],
    data_atualizacao: new Date()
  },
  {
    produto_id: 13,
    lojista_id: 102,
    nome: "Fogareiro Portátil para Camping Ultraleve",
    categoria: "Cozinha Outdoor",
    marca: "CampChef",
    schema_version: 1,
    atributos: {
      tipo_gas: "Butano/Propano",
      potencia_watts: 3000,
      acendimento_automatico: true,
      peso_gramas: 120
    },
    tags: ["camping", "cozinha", "fogareiro"],
    data_atualizacao: new Date()
  }
]);

print("Produtos do catálogo cadastrados com sucesso no MongoDB!");

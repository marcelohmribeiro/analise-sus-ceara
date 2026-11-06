## Relatório: como o enriquecimento foi feito

### 1. Bases utilizadas
| Base | Fonte | Campos usados |
|---|---|---|
| Atendimentos SUS | Arquivo da atividade (204.579 registros) | id, município, primeiro nome |
| Municípios do CE | API de Localidades do IBGE | código IBGE, nome oficial, mesorregião, região intermediária |
| Censo 2022 | IBGE/SIDRA, tabela 4714 | população, área (km²), densidade (hab/km²) |
| PIB dos Municípios 2023 | IBGE/SIDRA, tabela 5938 | PIB → PIB per capita |
| Coordenadas | Repositório público `kelvins/municipios-brasileiros` | latitude, longitude (para o mapa) |

> O IDH municipal (Atlas Brasil, 2010) não está disponível em API aberta do IBGE e está defasado, por isso usamos o **PIB per capita 2023** como indicador socioeconômico.

### 2. Tratamento e padronização
- Removidos os espaços em branco à direita do nome do município (o campo vinha com tamanho fixo).
- Criada uma **chave de junção**: nome sem acentos, em maiúsculas, sem hífens nem apóstrofos e com espaços simples. Isso faz `MARACANAÚ` e `Maracanaú` virarem a mesma chave.
- Grafia antiga corrigida: **ITAPAGÉ → Itapajé** (1.070 registros). O município mudou oficialmente de nome e, sem a correção, esses registros ficariam de fora.
- Conferidos IDs inválidos ou duplicados, linhas duplicadas e campos vazios. Havia apenas 1 registro sem primeiro nome, que foi mantido porque não afeta a contagem por município.

### 3. Junção (enriquecimento)
Junção à esquerda (*left join*) dos atendimentos com a tabela de municípios do IBGE pela chave normalizada. Depois, junção pelo **código IBGE** com população, PIB e coordenadas, que é uma chave numérica e sem ambiguidade.
Resultado: **100% dos registros casados** e **184 de 184 municípios** do Ceará com atendimentos.

### 4. Coesão dos dados
- **Confirmada.** Nenhum município tem mais atendimentos que habitantes. O maior valor é de 8,4% da população (Penaforte).
- Todos os municípios da base pertencem ao Ceará e existem no IBGE.
- Não há IDs nem registros duplicados.
- A relação entre população e atendimentos é positiva (correlação de Pearson de 0,65), como seria de esperar.

### 5. Análises e justificativas
1. **Volume por mesorregião e município.** Mostra onde está a carga absoluta de atendimentos.
2. **Atendimentos por 100 mil habitantes.** Remove o efeito do tamanho da cidade e permite comparar municípios grandes e pequenos.
3. **Ranking de maiores e menores taxas.** Identifica possíveis pontos de sobrecarga ou de baixa cobertura.
4. **Mapa interativo.** Mostra a distribuição geográfica, com o tamanho do círculo indicando o volume e a cor indicando a taxa.
5. **Perfil socioeconômico.** Testa se a taxa de atendimentos está associada à renda (PIB per capita) e à densidade demográfica.

### 6. Principais insights
- O **Noroeste Cearense** tem mais atendimentos (49.953) que a **Metropolitana de Fortaleza** (27.949), embora a Metropolitana concentre 41% da população do estado.
- Em taxa, a Metropolitana tem a menor do estado (777 por 100 mil). O **Norte Cearense** tem a maior (4.051 por 100 mil).
- **Fortaleza** lidera em volume (9.364), mas tem a menor taxa entre os municípios com dados completos (386 por 100 mil).
- **Penaforte, Tejuçuoca e Itatira** têm as maiores taxas, acima de 7.700 por 100 mil.
- A correlação de Spearman da taxa é negativa com o PIB per capita (−0,30) e com a densidade (−0,22). Ou seja, municípios mais pobres e menos densos atendem proporcionalmente mais pelo SUS.

"""Trata a base de atendimentos, junta com os dados do IBGE e gera os arquivos usados pelo app."""
import json
import unicodedata
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
RAW = DATA / "raw"

# Grafias antigas presentes na base de atendimentos -> nome oficial atual do IBGE (já normalizado).
ALIASES = {"ITAPAGE": "ITAPAJE"}


def normalizar(nome: str) -> str:
    """Remove acentos, espaços extras e deixa em maiúsculas para servir de chave de junção."""
    sem_acento = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.upper().replace("'", "").replace("-", " ").split())


def sidra(arquivo: str) -> pd.DataFrame:
    """Lê um JSON da API SIDRA, pulando a linha de cabeçalho."""
    df = pd.DataFrame(json.load(open(RAW / arquivo, encoding="utf-8"))[1:])
    df["V"] = pd.to_numeric(df["V"], errors="coerce")
    return df


def carregar_ibge() -> pd.DataFrame:
    munis = json.load(open(RAW / "munis.json", encoding="utf-8"))
    ibge = pd.DataFrame(
        {
            "cod_ibge": str(m["id"]),
            "municipio_ibge": m["nome"],
            "uf": "CE",
            "mesorregiao": m["microrregiao"]["mesorregiao"]["nome"],
            "regiao_intermediaria": m["regiao-imediata"]["regiao-intermediaria"]["nome"],
        }
        for m in munis
    )

    censo = sidra("censo.json").pivot_table(index="D1C", columns="D2C", values="V")
    censo = censo.rename(columns={"93": "populacao_2022", "6318": "area_km2", "614": "densidade_hab_km2"})
    ibge = ibge.merge(censo, left_on="cod_ibge", right_index=True, how="left")

    pib = sidra("pib.json")[["D1C", "V", "D3N"]].rename(columns={"D1C": "cod_ibge", "V": "pib_mil_reais"})
    ano_pib = pib["D3N"].iloc[0]
    ibge = ibge.merge(pib.drop(columns="D3N"), on="cod_ibge", how="left")
    ibge["pib_per_capita"] = ibge["pib_mil_reais"] * 1000 / ibge["populacao_2022"]

    coords = pd.read_csv(RAW / "coords.csv", dtype={"codigo_ibge": str})
    ibge = ibge.merge(
        coords[["codigo_ibge", "latitude", "longitude"]], left_on="cod_ibge", right_on="codigo_ibge", how="left"
    ).drop(columns="codigo_ibge")

    ibge["chave"] = ibge["municipio_ibge"].map(normalizar)
    print(f"IBGE: {len(ibge)} municípios do CE (PIB de {ano_pib})")
    return ibge


def carregar_atendimentos() -> tuple[pd.DataFrame, dict]:
    bruto = pd.read_csv(DATA / "atendimentos.csv", dtype=str, encoding="utf-8")
    bruto.columns = ["id", "municipio", "primeiro_nome"]
    qualidade = {"linhas_brutas": len(bruto)}

    df = bruto.copy()
    df["municipio"] = df["municipio"].str.strip()
    df["primeiro_nome"] = df["primeiro_nome"].str.strip().str.upper()
    df["id"] = pd.to_numeric(df["id"], errors="coerce")

    qualidade["id_invalido"] = int(df["id"].isna().sum())
    qualidade["id_duplicado"] = int(df["id"].duplicated().sum())
    qualidade["municipio_vazio"] = int((df["municipio"].fillna("") == "").sum())
    qualidade["nome_vazio"] = int((df["primeiro_nome"].fillna("") == "").sum())
    qualidade["linhas_duplicadas"] = int(df.duplicated().sum())

    df = df.dropna(subset=["id"]).drop_duplicates(subset=["id"])
    df = df[df["municipio"].fillna("") != ""]
    df["chave"] = df["municipio"].map(normalizar)
    corrigidos = df["chave"].isin(ALIASES)
    qualidade["nomes_corrigidos"] = df.loc[corrigidos, "municipio"].value_counts().to_dict()
    df["chave"] = df["chave"].replace(ALIASES)
    qualidade["linhas_validas"] = len(df)
    return df, qualidade


def main() -> None:
    ibge = carregar_ibge()
    atend, qualidade = carregar_atendimentos()

    base = atend.merge(ibge, on="chave", how="left", indicator=True)
    sem_par = base.loc[base["_merge"] == "left_only", "municipio"].value_counts()
    qualidade["municipios_sem_par"] = sem_par.to_dict()
    qualidade["atendimentos_sem_par"] = int(sem_par.sum())
    base = base[base["_merge"] == "both"].drop(columns=["_merge", "chave"])

    resumo = base.groupby("cod_ibge").size().rename("atendimentos").reset_index()
    resumo = ibge.drop(columns="chave").merge(resumo, on="cod_ibge", how="left")
    resumo["atendimentos"] = resumo["atendimentos"].fillna(0).astype(int)
    resumo["atend_por_100k"] = resumo["atendimentos"] / resumo["populacao_2022"] * 100_000
    resumo["pct_populacao"] = resumo["atendimentos"] / resumo["populacao_2022"] * 100
    resumo["mais_atend_que_hab"] = resumo["atendimentos"] > resumo["populacao_2022"]

    qualidade["municipios_ibge"] = len(ibge)
    qualidade["municipios_com_atendimento"] = int((resumo["atendimentos"] > 0).sum())
    qualidade["municipios_mais_atend_que_hab"] = int(resumo["mais_atend_que_hab"].sum())

    nomes = base.groupby(["mesorregiao", "primeiro_nome"]).size().rename("atendimentos").reset_index()

    base.to_csv(DATA / "base_enriquecida.csv", index=False)
    nomes.to_csv(DATA / "nomes_por_regiao.csv", index=False)
    resumo.to_csv(DATA / "resumo_municipios.csv", index=False)
    json.dump(qualidade, open(DATA / "qualidade.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(qualidade, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

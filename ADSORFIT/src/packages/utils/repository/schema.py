from __future__ import annotations

from sqlalchemy import Column, Float, Integer, BigInteger, String, UniqueConstraint
from sqlalchemy.orm import declarative_base


Base = declarative_base()


###############################################################################
class AdsorptionBestFit(Base):
    __tablename__ = "ADSORPTION_BEST_FIT"
    id = Column(Integer, primary_key=True)
    experiment = Column(String)
    temperature_K = Column("temperature [K]", BigInteger)
    pressure_Pa = Column("pressure [Pa]", String)
    uptake_mol_g = Column("uptake [mol/g]", String)
    measurement_count = Column(BigInteger)
    min_pressure = Column(Float)
    max_pressure = Column(Float)
    min_uptake = Column(Float)
    max_uptake = Column(Float)
    langmuir_lss = Column("Langmuir LSS", Float)
    langmuir_k = Column("Langmuir k", Float)
    langmuir_k_error = Column("Langmuir k error", Float)
    langmuir_qsat = Column("Langmuir qsat", Float)
    langmuir_qsat_error = Column("Langmuir qsat error", Float)
    sips_lss = Column("Sips LSS", Float)
    sips_k = Column("Sips k", Float)
    sips_k_error = Column("Sips k error", Float)
    sips_qsat = Column("Sips qsat", Float)
    sips_qsat_error = Column("Sips qsat error", Float)
    sips_exponent = Column("Sips exponent", Float)
    sips_exponent_error = Column("Sips exponent error", Float)
    freundlich_lss = Column("Freundlich LSS", Float)
    freundlich_k = Column("Freundlich k", Float)
    freundlich_k_error = Column("Freundlich k error", Float)
    freundlich_exponent = Column("Freundlich exponent", Float)
    freundlich_exponent_error = Column("Freundlich exponent error", Float)
    temkin_lss = Column("Temkin LSS", Float)
    temkin_k = Column("Temkin k", Float)
    temkin_k_error = Column("Temkin k error", Float)
    temkin_beta = Column("Temkin beta", Float)
    temkin_beta_error = Column("Temkin beta error", Float)
    best_model = Column("best model", String)
    worst_model = Column("worst model", String)
    __table_args__ = (UniqueConstraint("id"),)

###############################################################################
class AdsorptionData(Base):
    __tablename__ = "ADSORPTION_DATA"
    id = Column(Integer, primary_key=True)
    experiment = Column(String)
    temperature_K = Column("temperature [K]", BigInteger)
    pressure_Pa = Column("pressure [Pa]", Float)
    uptake_mol_g = Column("uptake [mol/g]", Float)
    __table_args__ = (UniqueConstraint("id"),)

###############################################################################
class AdsorptionFittingResults(Base):
    __tablename__ = "ADSORPTION_FITTING_RESULTS"
    id = Column(Integer, primary_key=True)
    experiment = Column(String)
    temperature_K = Column("temperature [K]", BigInteger)
    pressure_Pa = Column("pressure [Pa]", String)
    uptake_mol_g = Column("uptake [mol/g]", String)
    measurement_count = Column(BigInteger)
    min_pressure = Column(Float)
    max_pressure = Column(Float)
    min_uptake = Column(Float)
    max_uptake = Column(Float)
    langmuir_lss = Column("Langmuir LSS", Float)
    langmuir_k = Column("Langmuir k", Float)
    langmuir_k_error = Column("Langmuir k error", Float)
    langmuir_qsat = Column("Langmuir qsat", Float)
    langmuir_qsat_error = Column("Langmuir qsat error", Float)
    sips_lss = Column("Sips LSS", Float)
    sips_k = Column("Sips k", Float)
    sips_k_error = Column("Sips k error", Float)
    sips_qsat = Column("Sips qsat", Float)
    sips_qsat_error = Column("Sips qsat error", Float)
    sips_exponent = Column("Sips exponent", Float)
    sips_exponent_error = Column("Sips exponent error", Float)
    freundlich_lss = Column("Freundlich LSS", Float)
    freundlich_k = Column("Freundlich k", Float)
    freundlich_k_error = Column("Freundlich k error", Float)
    freundlich_exponent = Column("Freundlich exponent", Float)
    freundlich_exponent_error = Column("Freundlich exponent error", Float)
    temkin_lss = Column("Temkin LSS", Float)
    temkin_k = Column("Temkin k", Float)
    temkin_k_error = Column("Temkin k error", Float)
    temkin_beta = Column("Temkin beta", Float)
    temkin_beta_error = Column("Temkin beta error", Float)
    __table_args__ = (UniqueConstraint("id"),)
    

###############################################################################
class AdsorptionProcessedData(Base):
    __tablename__ = "ADSORPTION_PROCESSED_DATA"
    id = Column(Integer, primary_key=True)
    experiment = Column(String)
    temperature_K = Column("temperature [K]", BigInteger)
    pressure_Pa = Column("pressure [Pa]", String)
    uptake_mol_g = Column("uptake [mol/g]", String)
    measurement_count = Column(BigInteger)
    min_pressure = Column(Float)
    max_pressure = Column(Float)
    min_uptake = Column(Float)
    max_uptake = Column(Float)
    __table_args__ = (UniqueConstraint("id"),)

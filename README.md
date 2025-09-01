<img src="https://afs-services.com/wp-content/uploads/2025/09/pypricing_banner.png" alt="RV Banner" style="width: 100%; height: auto; display: block;">

##
This repository provides a Python library for pricing and risk management of a wide range of financial products, including structured products, credit derivatives, and fixed-income instruments, with modular models and Monte Carlo engines.  
- The central documentation is available at **https://arfima.pages.arfima.com/afs/pypricing**, which includes installation instructions and tutorials.

## Project Overview

PyPricing is designed to deliver a flexible platform for quantitative analysts and developers to implement, calibrate, and deploy pricing models and risk metrics. Key features include:

- Modular architecture separating data ingestion, pricing models, and risk analytics  
- Support for both analytical and simulation-based pricing (Black-Scholes, HJM, Hull-White, LMM, etc.)  
- Tools for building cash-flow schedules, handling market data (calendars, curves), and computing Greeks  
- Integration with Jupyter notebooks for interactive exploration and prototyping

## Repository Structure

### Data Ingestion
- **`data/`**: market data ingestion and calendar utilities  
- **`data/calendars.py`**: business-day conventions and holiday calendars  
- **`data/yields.py`**: bootstrapping and interpolation of yield curves  

### Pricing Models
- **`pricing/`**: core pricing engines for various product classes  
- **`pricing/option.py`**: Black-Scholes, Merton, and local volatility models  
- **`pricing/interest_rate/`**: HJM, Hull-White, and LIBOR Market Model implementations  
- **`pricing/credit/`**: Credit Default Swap and credit spread frameworks  
- **`pricing/structured/`**: structured product wrappers and simulation engines  

### Risk Analytics
- **`risk/`**: risk-and sensitivity-analysis modules  
- **`risk/greeks.py`**: analytical Greeks and finite-difference approximations  
- **`risk/var.py`**: historical and Monte Carlo Value-at-Risk  
- **`risk/market_risk.py`**: factor sensitivities and stress-testing tools  

### Examples & Notebooks
- **`examples/`**: standalone Python scripts demonstrating common workflows  
- **`notebooks/`**: Jupyter notebooks with tutorials, case studies, and interactive demos  

### Testing & CI
- **`tests/`**: pytest suite covering pricing and risk modules  
- **`.gitlab-ci.yml`**: CI/CD pipeline configuration for automated testing and linting  
- **`.pre-commit-config.yaml`**: pre-commit hooks for code formatting and quality checks  

### Documentation & Dependencies
- **`docs/`**: Sphinx source files for the online documentation  
- **`requirements.txt`**: list of Python dependencies required to run the library and notebooks  
- **`LICENSE`**: Creative Commons Attribution-NonCommercial 4.0 International  

## Acknowledgements

This work has been supported by the Government of Spain (Ministerio de Ciencia e Innovación) and the European Union through Project CPP2021-008644 / AEI / 10.13039/501100011033 / Unión Europea Next GenerationEU / PRTR. Visit our website for more information [Green and Digital Finance – Next GenerationEU](https://afs-services.com/proyectos-nextgen-eu/).

<p align="center">
  <img
    src="https://afs-services.com/wp-content/uploads/2025/06/logomciaienetgeneration-1232x264.png"
    alt="Logo MCIAI NetGeneration"
    height="100"
  >
</p>
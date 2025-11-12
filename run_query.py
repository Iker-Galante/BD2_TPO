#!/usr/bin/env python
"""
Helper script to run queries without needing to set PYTHONPATH manually.
Usage: python run_query.py <query_number>
Example: python run_query.py 1
"""

import sys
import os
import subprocess

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_query.py <query_number>")
        print("Example: python run_query.py 1")
        print("\nAvailable queries:")
        print("  1  - Clientes activos con sus pólizas vigentes")
        print("  2  - Siniestros abiertos con tipo, monto y cliente afectado")
        print("  3  - Vehículos asegurados con su cliente y póliza")
        print("  4  - Clientes sin pólizas activas")
        print("  5  - Agentes activos con cantidad de pólizas asignadas")
        print("  6  - Pólizas vencidas con el nombre del cliente")
        print("  7  - Top 10 clientes por cobertura total")
        print("  8  - Siniestros tipo 'Accidente' del último año")
        print("  9  - Vista de pólizas activas ordenadas por fecha de inicio")
        print("  10 - Pólizas suspendidas con estado del cliente")
        print("  11 - Clientes con más de un vehículo asegurado")
        print("  12 - Agentes y cantidad de siniestros asociados")
        print("  13 - ABM de clientes (ejemplos)")
        print("  14 - Alta de nuevos siniestros (ejemplos)")
        print("  15 - Emisión de nuevas pólizas (ejemplos)")
        sys.exit(1)
    
    query_num = sys.argv[1]
    query_file = f"app/queries/query{query_num}.py"
    
    if not os.path.exists(query_file):
        print(f"Error: Query file '{query_file}' not found")
        sys.exit(1)
    
    # Import and run the query module
    try:
        # Change to project directory
        os.chdir(project_root)
        
        # Run the query file
        with open(query_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        exec(code, {'__name__': '__main__', '__file__': query_file})
    except Exception as e:
        print(f"Error executing query: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

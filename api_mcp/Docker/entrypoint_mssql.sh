#!/bin/bash

/opt/mssql/bin/sqlservr &

echo "Esperando a que SQL Server inicie..."
sleep 30

for i in {1..50}; do
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "SELECT 1" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "SQL Server listo"
        break
    fi
    echo "Esperando SQL Server... intento $i"
    sleep 2
done

echo "Verificando base de datos ${MSSQL_DATABASE}..."
DB_EXISTS=$(/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.databases WHERE name = '${MSSQL_DATABASE}'" -h -1 | tr -d ' ')

if [ "$DB_EXISTS" -eq "0" ]; then
    echo "Creando base de datos ${MSSQL_DATABASE}..."
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "CREATE DATABASE [${MSSQL_DATABASE}]"
    echo "Base de datos ${MSSQL_DATABASE} creada"
else
    echo "Base de datos ${MSSQL_DATABASE} ya existe"
fi

echo "Verificando tabla SAP_EMPRESAS..."
TABLE_EXISTS=$(/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -d "${MSSQL_DATABASE}" -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'SAP_EMPRESAS'" -h -1 | tr -d ' ')

if [ "$TABLE_EXISTS" -eq "0" ]; then
    echo "Creando tabla SAP_EMPRESAS..."
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -d "${MSSQL_DATABASE}" -Q "
    CREATE TABLE SAP_EMPRESAS (
        Instancia NVARCHAR(100) NOT NULL,
        Prueba BIT NOT NULL DEFAULT 0,
        ServiceLayer BIT NOT NULL DEFAULT 0,
        PrintHeadr NVARCHAR(255),
        CompnyAddr NVARCHAR(500),
        TaxIdNum NVARCHAR(50),
        PRIMARY KEY (Instancia)
    )"
    echo "Tabla SAP_EMPRESAS creada"
else
    echo "Tabla SAP_EMPRESAS ya existe"
fi

wait

def receive_data_file_result(payload):
    """
    Recibe el resultado del guardado de archivo de datos. Si es ok, procesa el resumen. informa a process_data
    parametros:
        payload: dict con 'Result' y 'details'
    retorna:
    """

    result = payload.get("Result")
    details = payload.get("details", {})

    if result == "Data saved":
        symbol = details.get("symbol", "UNKNOWN")
        timeframe = details.get("timeframe", "UNKNOWN")

        print(
            f"[Data File Saved] {symbol}_{timeframe}"
            f" rows={details.get('stored_rows', 0)}"   
        )

        # Llamar a process_data para procesar el archivo guardado
        ##utils.process_data(file_path)
    else:
        print(f"[Data File Save Error] Result: {result}")

def send_data_file_result(result_payload):
    """
    Confirma el guardado de archivo de datos del instrumento-timeframe al microservicio process_data.
    parametros:
        result_payload: dict con 'Result' y 'details'
    """
    pass
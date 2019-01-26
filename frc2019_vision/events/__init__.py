def assemble_message(message: str, error: bool = False) -> str:
    print("Assembling Message")
    if error:
        message = "-ERR {0}".format(message)
    else:
        message = "+OK {0}".format(message)

    return message

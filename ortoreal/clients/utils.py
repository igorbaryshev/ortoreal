def client_directory_path(instance, filename):
    """
    Название директория для файлов клиента.
    """
    return f"clients/{instance.id}/{filename}"

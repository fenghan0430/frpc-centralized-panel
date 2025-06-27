def get_manager_from_main():
    """从main.py中获取get_manager函数

    Returns:
        main.get_manager: 获取main.py中的get_manager函数
    """
    from main import get_manager
    return get_manager()

def get_logger_from_main():
    """从main.py中获取get_logger函数

    Returns:
        main.get_logger: 获取main.py中的get_logger函数
    """
    from main import get_logger
    return get_logger()

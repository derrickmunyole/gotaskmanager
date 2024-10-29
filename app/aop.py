import json

from app import db

from app.models import Activities


def log_activity(action_type, target_type):
    """
    A decorator to log user activities.

    This decorator logs the activity of a function by creating an entry in the Activities table.
    It captures the user ID, action type, target type, and optionally the target ID if the result
    of the function has an 'id' attribute.

    Args:
        action_type (str): The type of action being logged (e.g., 'create', 'update').
        target_type (str): The type of target the action is performed on (e.g., 'post', 'comment').

    Returns:
        function: A wrapped function that logs the activity when called.
    """

    def decorator(func):
        """
        Inner decorator function that wraps the original function.

        Args:
            func (function): The function to be wrapped and logged.

        Returns:
            function: The wrapped function with logging capability.
        """

        def wrapper(*args, **kwargs):
            """
            Wrapper function that executes the original function and logs the activity.

            Args:
                *args: Positional arguments for the original function.
                **kwargs: Keyword arguments for the original function.

            Returns:
                Any: The result of the original function execution.
            """
            try:
                result = func(*args, **kwargs)

                current_user = kwargs.get('current_user')

                if current_user:
                    details = {
                        'actor': current_user.username,
                        'action': action_type,
                        'target': target_type,
                        'task_title': result.title if hasattr(result, 'title') else None
                    }

                    activity = Activities(
                        user_id=current_user.id,
                        action_type=action_type,
                        target_type=target_type,
                        target_id=result.id if hasattr(result, 'id') else None,
                        details=json.dumps(details)
                    )
                    db.session.add(activity)
                    db.session.commit()
                    return result
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
                return func(*args, **kwargs)

        return wrapper

    return decorator

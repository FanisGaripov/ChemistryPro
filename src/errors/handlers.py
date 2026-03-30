import http

from flask import render_template
import flask_login


def register_error_handlers(app):
    @app.errorhandler(http.HTTPStatus.NOT_FOUND)
    def page_not_found(e):
        """404 - Страницы не существует"""
        user = flask_login.current_user
        return (
            render_template(
                f"errors/{http.HTTPStatus.NOT_FOUND}.html", user=user
            ),
            http.HTTPStatus.NOT_FOUND,
        )

    @app.errorhandler(http.HTTPStatus.UNAUTHORIZED)
    def unauthorized_error(e):
        """401 - Не авторизован"""
        user = flask_login.current_user
        return (
            render_template(
                f"errors/{http.HTTPStatus.UNAUTHORIZED}.html",
                user=user,
                error=e,
            ),
            http.HTTPStatus.UNAUTHORIZED,
        )

    @app.errorhandler(http.HTTPStatus.CONFLICT)
    def conflict_error(e):
        """409 - Пользователь уже существует"""
        user = flask_login.current_user
        return (
            render_template(
                f"errors/{http.HTTPStatus.CONFLICT}.html", user=user, error=e
            ),
            http.HTTPStatus.CONFLICT,
        )

    @app.errorhandler(http.HTTPStatus.BAD_REQUEST)
    def bad_request_error(e):
        """400 - Неверный формат данных"""
        user = flask_login.current_user
        return (
            render_template(
                f"errors/{http.HTTPStatus.BAD_REQUEST}.html",
                user=user,
                error=e,
            ),
            http.HTTPStatus.BAD_REQUEST,
        )

    @app.errorhandler(http.HTTPStatus.INTERNAL_SERVER_ERROR)
    def internal_server_error(e):
        """500 - Внутренная ошибка сервера"""
        user = flask_login.current_user
        return (
            render_template(
                f"errors/{http.HTTPStatus.INTERNAL_SERVER_ERROR}.html",
                user=user,
                error=e,
            ),
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )

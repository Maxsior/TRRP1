import os.path
from googleapiclient.discovery import build
from oauthlib.oauth2.rfc6749.errors import AccessDeniedError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import click
import pyAesCrypt
from getpass import getpass
import io
import json


def _auth():
    BUFFER_SIZE = 64 * 1024
    SCOPES = ['https://www.googleapis.com/auth/tasks']
    creds = None
    if os.path.exists('token.aes'):
        password = getpass('Введите пароль: ')
        creds_stream = io.BytesIO()
        filesize = os.path.getsize('token.aes')
        with open('token.aes', 'rb') as token:
            try:
                pyAesCrypt.decryptStream(token, creds_stream, password, BUFFER_SIZE, filesize)
                creds_json = json.loads(creds_stream.getvalue().decode())
                creds = Credentials.from_authorized_user_info(creds_json, SCOPES)
            except (ValueError, json.decoder.JSONDecodeError):
                print('Неверный пароль')
                exit(-1)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            try:
                creds = flow.run_local_server(port=0)
            except AccessDeniedError:
                print('Доступ не предоставлен')
                exit(-1)

        with open('token.aes', 'wb') as token:
            password = getpass('Придумайте пароль: ')
            cred_stream = io.BytesIO(creds.to_json().encode('utf8'))
            pyAesCrypt.encryptStream(cred_stream, token, password, BUFFER_SIZE)
    return build('tasks', 'v1', credentials=creds)


@click.group()
def tasks():
    pass


@tasks.command()
@click.option('--title', '-t', prompt=True, type=str)
@click.option('--notes', '-d', type=str, default='')
@click.option('--completed', '-c', default=False, show_default=True, is_flag=True)
def create(title, notes, completed):
    api = _auth()
    api.tasks().insert(
        tasklist='@default',
        body={
            "title": title,
            "notes": notes,
            "status": 'completed' if completed else 'needsAction',
        }
    ).execute()
    click.echo(f'Task "{title}" was created')


@tasks.command()
def get():
    api = _auth()
    r = api.tasks().list(tasklist='@default', showHidden=True).execute()
    tasks = r.get('items', [])
    for i, task in enumerate(tasks):
        click.echo(f"{i}. [{'v' if 'completed' in task else ' '}] {task['title']}")


@tasks.command()
@click.option('--number', '-n', prompt=True, type=int, required=True)
@click.option('--title', '-t', type=str)
@click.option('--notes', '-d', type=str, default='')
@click.option('--completed', '-c', default=False, show_default=True, is_flag=True)
@click.option('--incompleted', '-ic', default=False, show_default=True, is_flag=True)
def update(number, title, notes, completed, incompleted):
    api = _auth()
    r = api.tasks().list(tasklist='@default').execute()
    tasks = r.get('items', [])
    body = {}
    if title:
        body['title'] = title
    if notes:
        body['notes'] = notes
    if completed:
        body['status'] = 'completed'
    if incompleted:
        body['status'] = 'needsAction'

    api.tasks().patch(
        tasklist='@default',
        task=tasks[number]['id'],
        body=body
    ).execute()
    click.echo('Done')


@tasks.command()
@click.option('--number', '-n', prompt=True, type=int, required=True)
def delete(number):
    api = _auth()
    r = api.tasks().list(tasklist='@default').execute()
    tasks = r.get('items', [])
    api.tasks().delete(tasklist='@default', task=tasks[number]['id']).execute()
    click.echo('Done')


if __name__ == '__main__':
    tasks()
    # _auth()
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import click


def _auth():
    SCOPES = ['https://www.googleapis.com/auth/tasks']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

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
@click.option('--title', '-t', prompt=True, type=str)
@click.option('--notes', '-d', type=str, default='')
@click.option('--completed', '-c', default=False, show_default=True, is_flag=True)
def update(number, title, notes, completed):
    api = _auth()
    r = api.tasks().list(tasklist='@default').execute()
    tasks = r.get('items', [])
    api.tasks().patch(
        tasklist='@default',
        task=tasks[number]['id'],
        body={
            "title": title,
            "notes": notes,
            "status": 'completed' if completed else 'needsAction',
        }).execute()
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

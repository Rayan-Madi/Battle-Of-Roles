"""
Script de gestion pour Battle of Roles
Commandes utiles pour gérer la base de données et l'application
"""
import click
from app import create_app, db
from app.models import User, Game, Turn
import secrets

app = create_app()


@click.group()
def cli():
    """Battle of Roles - Script de gestion"""
    pass


@cli.command('init-db')
def init_db():
    """Initialise la base de données"""
    click.echo("🔧 Initialisation de la base de données...")
    with app.app_context():
        db.create_all()
        click.echo("✅ Base de données initialisée avec succès!")


@cli.command('test-connection')
def test_connection():
    """Teste la connexion à la base de données"""
    click.echo("🔌 Test de connexion à la base de données...")
    try:
        with app.app_context():
            result = db.session.execute(db.text('SELECT 1')).fetchone()
            if result:
                click.echo("✅ Connexion à la base de données réussie!")
                
                users_count = User.query.count()
                games_count = Game.query.count()
                
                click.echo(f"📊 Données actuelles:")
                click.echo(f"   - {users_count} utilisateur(s)")
                click.echo(f"   - {games_count} partie(s)")
            else:
                click.echo("❌ Erreur de connexion.")
    except Exception as e:
        click.echo(f"❌ Erreur: {e}")


@cli.command()
def stats():
    """Affiche les statistiques globales"""
    with app.app_context():
        total_users = User.query.count()
        total_guests = User.query.filter_by(is_guest=True).count()
        total_registered = total_users - total_guests
        total_games = Game.query.count()
        finished_games = Game.query.filter_by(status='finished').count()
        ongoing_games = Game.query.filter_by(status='ongoing').count()
        
        click.echo("\n📊 Statistiques globales de Battle of Roles")
        click.echo("=" * 60)
        click.echo(f"👥 Utilisateurs:")
        click.echo(f"   - Total: {total_users}")
        click.echo(f"   - Comptes enregistrés: {total_registered}")
        click.echo(f"   - Invités: {total_guests}")
        click.echo(f"\n🎮 Parties:")
        click.echo(f"   - Total: {total_games}")
        click.echo(f"   - Terminées: {finished_games}")
        click.echo(f"   - En cours: {ongoing_games}")
        
        click.echo("=" * 60)


if __name__ == '__main__':
    cli()
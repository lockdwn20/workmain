# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    
    # Start PostgreSQL
    sudo service postgresql start
else
    echo "✓ PostgreSQL already installed"
fi

# Create database and user
sudo -u postgres psql << 'EOSQL'
-- Create user
CREATE USER workmain_user WITH PASSWORD 'workmain_dev_pass';

-- Create database
CREATE DATABASE workmain OWNER workmain_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE workmain TO workmain_user;

-- Connect to database and grant schema privileges
\c workmain
GRANT ALL ON SCHEMA public TO workmain_user;
EOSQL

echo "✓ Database 'workmain' created with user 'workmain_user'"

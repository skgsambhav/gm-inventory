# 📦 Modern Flask Inventory Management System

A beautiful, modern inventory management application built with Flask, featuring a smooth UI/UX with dark mode support, comprehensive CRUD operations, and advanced features like bulk import/export.

## ✨ Features

### Core Functionality
- ✅ **Full CRUD Operations** - Create, read, update, and delete inventory items
- 📊 **Advanced Search & Filtering** - Search by description, group, supplier
- 📄 **Pagination** - Efficient browsing of large datasets
- 📥 **Bulk Import** - CSV and Excel file import with duplicate detection
- 📤 **Export to CSV** - Export selected or all items
- 📋 **WhatsApp-Ready Copying** - Copy items in WhatsApp-friendly format
- 💰 **Auto Margin Calculation** - Real-time profit margin indicators

### User Experience
- 🌓 **Dark Mode Support** - Toggle between light and dark themes with persistent preference
- 🎨 **Modern UI/UX** - Smooth animations and transitions throughout
- 📱 **Fully Responsive** - Optimized for mobile, tablet, and desktop
- ⚡ **Fast Performance** - Optimized queries and efficient pagination
- 🎯 **Intuitive Interface** - User-friendly forms with smart auto-parsing
- 🔔 **Toast Notifications** - Non-intrusive user feedback

### Technical Features
- 🏗️ **Application Factory Pattern** - Clean, scalable architecture
- 🔒 **Data Validation** - Server-side and client-side validation
- 📊 **Database Constraints** - Ensures data integrity
- 🔍 **Indexed Fields** - Fast search performance
- 🎨 **CSS Variables** - Easy theme customization
- ♿ **Accessibility** - ARIA labels and keyboard navigation support

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd flask_inventory_app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   ```
   http://localhost:5000
   ```

## 📁 Project Structure

```
flask_inventory_app/
├── app.py                  # Application factory and error handlers
├── config.py               # Configuration settings for different environments
├── models.py               # Database models with validation
├── extensions.py           # Flask extensions initialization
├── requirements.txt        # Python dependencies
├── routes/
│   ├── __init__.py
│   ├── add_item.py        # Item creation and editing routes
│   └── records.py         # Item listing, search, import/export routes
├── static/
│   └── css/
│       └── style.css      # Modern CSS with dark mode support
├── templates/
│   ├── base.html          # Base template with navigation and dark mode toggle
│   ├── add_item.html      # Item form with smart parsing
│   └── records.html       # Item listing with advanced features
└── instance/
    └── database.db        # SQLite database (auto-created)
```

## 🎨 UI Features

### Dark Mode
- Click the floating button in the bottom-right corner to toggle dark mode
- Your preference is saved automatically
- Smooth transitions between themes

### Smart Form Parsing
The add/edit item form includes intelligent parsing:
- **Group extraction**: Automatically extracts group from `(Group Name)` in description
- **MRP parsing**: Detects price patterns like `500/-`
- **Size parsing**: Understands formats like `1CTN=20PKD`
- **Real-time margin indicators**: Visual profit margin display with color coding

### Advanced Table Features
- **Column visibility toggle**: Show/hide columns as needed
- **Multi-select**: Select multiple items for batch operations
- **WhatsApp copy**: Copy items in chat-friendly format
- **CSV export**: Export visible columns only or selected items
- **Responsive design**: Optimized layout for all screen sizes

## 🔧 Configuration

### Environment Variables
```bash
FLASK_ENV=development          # development, production, testing
FLASK_SECRET=your-secret-key   # Session secret key
DATABASE_URL=sqlite:///database.db  # Database connection string
PORT=5000                      # Application port
```

### Database Configuration
The app uses SQLite by default. To use PostgreSQL or MySQL:

1. Install the appropriate driver:
   ```bash
   # PostgreSQL
   pip install psycopg2-binary

   # MySQL
   pip install pymysql
   ```

2. Update `DATABASE_URL` in config.py or set environment variable:
   ```
   postgresql://user:password@localhost/dbname
   mysql+pymysql://user:password@localhost/dbname
   ```

## 📊 Data Model

### Item Fields
- `id` - Unique identifier (auto-generated)
- `description` - Item name/description (required)
- `item_group` - Category/group
- `mrp` - Maximum Retail Price
- `item_size` - Package size (e.g., "1CTN=20PKD")
- `main_unit` - Main unit (e.g., "CTN")
- `alt_unit` - Alternative unit (e.g., "PKD")
- `alt_qty` - Alternative quantity
- `purc_price` - Purchase price
- `bulk_sp1` - Bulk sale price 1
- `bulk_sp2` - Bulk sale price 2
- `sale_price` - Regular sale price
- `supplier` - Supplier name
- `last_updated` - Last modification timestamp
- `created_at` - Creation timestamp

## 🛠️ Development

### Running in Development Mode
```bash
python app.py
```
This runs the app with debug mode enabled and auto-reload on file changes.

### Running in Production
```bash
FLASK_ENV=production gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

### Database Migrations
The app uses Flask-SQLAlchemy with automatic table creation. For more advanced migrations, consider adding Flask-Migrate.

## 📋 Import/Export

### Import Format
The app accepts CSV or Excel files (.csv, .xlsx, .xls) with the following columns:
- Description (required)
- Group
- MRP
- Size
- Main (unit)
- Alt (unit)
- Purchase (price)
- Bulk SP1
- Bulk SP2
- Sale (price)
- Supplier

**Note:** Column order doesn't matter, and column names are flexible (e.g., "Purchase Price" or "Purc Price" both work).

### Export Features
- Export all items or selected items only
- Exports visible columns based on your column visibility settings
- Includes UTF-8 BOM for Excel compatibility
- Timestamped filenames

## 🎯 Best Practices

1. **Regular Backups**: The SQLite database is in `instance/database.db` - back it up regularly
2. **Security**: Change the `SECRET_KEY` in production
3. **Performance**: For large datasets (10,000+ items), consider PostgreSQL
4. **Validation**: The app validates data on both client and server side
5. **Imports**: Preview your CSV/Excel file before importing to avoid duplicates

## 🐛 Troubleshooting

### Database Issues
```bash
# If database gets corrupted, delete and recreate:
rm instance/database.db
python app.py  # Will recreate database
```

### Import Errors
- Ensure CSV uses UTF-8 encoding
- Check column headers match expected names
- Verify numeric fields don't contain text

### Dark Mode Not Persisting
- Clear browser cache and localStorage
- Check browser privacy settings allow localStorage

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📧 Support

If you encounter any issues or have questions, please open an issue in the repository.

---

**Built with ❤️ using Flask, Bootstrap 5, and modern web technologies**

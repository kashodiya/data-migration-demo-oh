# Chinook SQLite Database Schema Documentation

**Generated on:** 2025-11-07 00:44:39  
**Database File:** Chinook_Sqlite.sqlite  
**File Size:** 0.96 MB (1,007,616 bytes)

## 📊 Database Overview

- **Total Tables:** 11
- **Total Records:** 15,607
- **Database Size:** 0.96 MB

## 📋 Table Summary

| Table Name | Row Count | Percentage |
|------------|-----------|------------|
| PlaylistTrack | 8,715 | 55.8% |
| Track | 3,503 | 22.4% |
| InvoiceLine | 2,240 | 14.4% |
| Invoice | 412 | 2.6% |
| Album | 347 | 2.2% |
| Artist | 275 | 1.8% |
| Customer | 59 | 0.4% |
| Genre | 25 | 0.2% |
| Playlist | 18 | 0.1% |
| Employee | 8 | 0.1% |
| MediaType | 5 | 0.0% |

## 🗂️ Detailed Table Schemas

### Artist Table
- **Purpose:** Stores music artists/bands
- **Records:** 275
- **Primary Key:** ArtistId
- **Columns:**
  - `ArtistId` (INTEGER, PK): Unique identifier
  - `Name` (NVARCHAR(120)): Artist name (2-85 chars, avg 20.57)

### Album Table
- **Purpose:** Stores music albums
- **Records:** 347
- **Primary Key:** AlbumId
- **Foreign Keys:** ArtistId → Artist.ArtistId
- **Columns:**
  - `AlbumId` (INTEGER, PK): Unique identifier
  - `Title` (NVARCHAR(160)): Album title (2-95 chars, avg 22.69)
  - `ArtistId` (INTEGER, FK): Reference to artist

### Track Table
- **Purpose:** Stores individual music tracks
- **Records:** 3,503 (largest content table)
- **Primary Key:** TrackId
- **Foreign Keys:** 
  - AlbumId → Album.AlbumId
  - MediaTypeId → MediaType.MediaTypeId
  - GenreId → Genre.GenreId
- **Key Statistics:**
  - Track names: 2-123 chars (avg 15.88)
  - Duration: 1,071ms - 5,286,953ms (avg 393,599ms ≈ 6.5 minutes)
  - File size: 38KB - 1GB (avg 33.5MB)
  - 27.9% of tracks missing composer information

### Genre Table
- **Purpose:** Music genre classifications
- **Records:** 25
- **Primary Key:** GenreId
- **Notable:** Covers genres from "Rock" to "Opera" (3-18 chars)

### MediaType Table
- **Purpose:** Audio file format types
- **Records:** 5
- **Primary Key:** MediaTypeId
- **Types:** MPEG audio, AAC audio, Protected AAC, Protected MPEG-4, Purchased AAC

### Playlist & PlaylistTrack Tables
- **Purpose:** User-created music playlists
- **Playlists:** 18 total
- **Playlist Tracks:** 8,715 (many-to-many relationship)
- **Note:** Largest table by record count due to track-playlist associations

### Customer Table
- **Purpose:** Store customer information
- **Records:** 59
- **Primary Key:** CustomerId
- **Foreign Keys:** SupportRepId → Employee.EmployeeId
- **Geographic Distribution:** 24 countries represented
- **Data Quality Notes:**
  - 83.1% missing company information
  - 79.7% missing fax numbers
  - 49.2% missing state information

### Employee Table
- **Purpose:** Company employee records
- **Records:** 8
- **Primary Key:** EmployeeId
- **Self-Referencing:** ReportsTo → Employee.EmployeeId
- **Roles:** 5 different job titles
- **Location:** All employees in Canada (AB province)

### Invoice & InvoiceLine Tables
- **Purpose:** Sales transaction records
- **Invoices:** 412 total
- **Invoice Lines:** 2,240 (detailed line items)
- **Price Range:** $0.99 - $25.86 per invoice
- **Average Invoice:** $5.65

## 🔗 Database Relationships

The Chinook database follows a well-normalized structure with clear relationships:

```
Artist (1) ──→ (M) Album (1) ──→ (M) Track
                                    ↓
Genre (1) ──→ (M) Track ←── (M) MediaType (1)
                ↓
PlaylistTrack (M) ←── (1) Playlist
                ↓
Customer (1) ──→ (M) Invoice (1) ──→ (M) InvoiceLine ──→ (1) Track
    ↓
Employee (1) ──→ (M) Customer
    ↓
Employee (self-referencing hierarchy)
```

### Key Relationships:
1. **Artist → Album → Track:** Music catalog hierarchy
2. **Track → Genre/MediaType:** Track categorization
3. **Playlist ↔ Track:** Many-to-many playlist management
4. **Customer → Invoice → InvoiceLine → Track:** Sales process
5. **Employee → Customer:** Support assignment
6. **Employee → Employee:** Management hierarchy

## 📈 Key Insights

### Data Distribution
- **Content Heavy:** 78.2% of records are in content tables (Track, PlaylistTrack)
- **Transaction Data:** 17.0% in sales tables (Invoice, InvoiceLine)
- **Reference Data:** 4.8% in lookup/reference tables

### Data Quality
- **High Completeness:** Core fields (names, IDs) are complete
- **Optional Fields:** Contact details often incomplete (fax, company)
- **Geographic Data:** Good international representation (24 countries)

### Business Model Indicators
- **Digital Music Store:** Focus on individual track sales ($0.99-$1.99)
- **Album-Centric:** Strong artist-album-track hierarchy
- **Playlist Features:** Extensive playlist functionality
- **Customer Support:** Dedicated support representatives

## 🎯 Use Cases

This database structure supports:
- **Music Catalog Management:** Artist, album, and track organization
- **Digital Sales:** Individual track and album purchases
- **Customer Management:** User accounts with support assignment
- **Playlist Creation:** User-generated music collections
- **Reporting & Analytics:** Sales, popularity, and customer insights

---

*This documentation was generated using automated database analysis tools. For technical details about the analysis process, see `database_analyzer.py`.*

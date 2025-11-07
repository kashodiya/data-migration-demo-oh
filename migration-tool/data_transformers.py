
"""
Data Transformers
Handles transformation of SQLite data to DynamoDB format
"""

from decimal import Decimal


class DataTransformers:
    """Transforms SQLite data to DynamoDB item format"""
    
    def transform_artist(self, artist_data):
        """Transform artist data to DynamoDB format"""
        return {
            'PK': {'S': f"ARTIST#{artist_data['ArtistId']}"},
            'SK': {'S': 'METADATA'},
            'EntityType': {'S': 'Artist'},
            'ArtistId': {'N': str(artist_data['ArtistId'])},
            'Name': {'S': artist_data['Name']},
            'AlbumCount': {'N': str(artist_data.get('AlbumCount', 0))},
            'TrackCount': {'N': str(artist_data.get('TrackCount', 0))},
            'GSI1PK': {'S': f"ARTIST_NAME#{artist_data['Name']}"},
            'GSI1SK': {'S': f"ARTIST#{artist_data['ArtistId']}"}
        }
    
    def transform_album(self, album_data):
        """Transform album data to DynamoDB format"""
        return {
            'PK': {'S': f"ARTIST#{album_data['ArtistId']}"},
            'SK': {'S': f"ALBUM#{album_data['AlbumId']}"},
            'EntityType': {'S': 'Album'},
            'AlbumId': {'N': str(album_data['AlbumId'])},
            'Title': {'S': album_data['Title']},
            'ArtistId': {'N': str(album_data['ArtistId'])},
            'ArtistName': {'S': album_data['ArtistName']},
            'TrackCount': {'N': str(album_data.get('TrackCount', 0))},
            'GSI1PK': {'S': f"ALBUM_TITLE#{album_data['Title']}"},
            'GSI1SK': {'S': f"ALBUM#{album_data['AlbumId']}"}
        }
    
    def transform_track(self, track_data):
        """Transform track data to DynamoDB format"""
        item = {
            'PK': {'S': f"ALBUM#{track_data['AlbumId']}"},
            'SK': {'S': f"TRACK#{track_data['TrackId']}"},
            'EntityType': {'S': 'Track'},
            'TrackId': {'N': str(track_data['TrackId'])},
            'Name': {'S': track_data['Name']},
            'AlbumId': {'N': str(track_data['AlbumId'])},
            'AlbumTitle': {'S': track_data['AlbumTitle']},
            'ArtistId': {'N': str(track_data['ArtistId'])},
            'ArtistName': {'S': track_data['ArtistName']},
            'UnitPrice': {'N': str(Decimal(str(track_data['UnitPrice'])))},
            'GSI1PK': {'S': f"TRACK_NAME#{track_data['Name']}"},
            'GSI1SK': {'S': f"TRACK#{track_data['TrackId']}"}
        }
        
        # Optional fields
        if track_data.get('Composer'):
            item['Composer'] = {'S': track_data['Composer']}
        
        if track_data.get('Milliseconds'):
            item['Milliseconds'] = {'N': str(track_data['Milliseconds'])}
        
        if track_data.get('Bytes'):
            item['Bytes'] = {'N': str(track_data['Bytes'])}
        
        if track_data.get('GenreId'):
            item['GenreId'] = {'N': str(track_data['GenreId'])}
            if track_data.get('GenreName'):
                item['GenreName'] = {'S': track_data['GenreName']}
                item['GSI2PK'] = {'S': f"GENRE#{track_data['GenreName']}"}
        
        if track_data.get('MediaTypeId'):
            item['MediaTypeId'] = {'N': str(track_data['MediaTypeId'])}
            if track_data.get('MediaTypeName'):
                item['MediaTypeName'] = {'S': track_data['MediaTypeName']}
        
        return item
    
    def transform_customer_profile(self, customer_data, orders_data):
        """Transform customer profile data to DynamoDB format"""
        item = {
            'PK': {'S': f"CUSTOMER#{customer_data['CustomerId']}"},
            'SK': {'S': 'PROFILE'},
            'EntityType': {'S': 'CustomerProfile'},
            'CustomerId': {'N': str(customer_data['CustomerId'])},
            'FirstName': {'S': customer_data['FirstName']},
            'LastName': {'S': customer_data['LastName']},
            'Email': {'S': customer_data['Email']},
            'Country': {'S': customer_data['Country']},
            'City': {'S': customer_data['City']},
            'TotalOrders': {'N': str(len(orders_data))},
            'GSI1PK': {'S': f"EMAIL#{customer_data['Email']}"},
            'GSI1SK': {'S': f"CUSTOMER#{customer_data['CustomerId']}"}
        }
        
        # Optional fields
        if customer_data.get('Company'):
            item['Company'] = {'S': customer_data['Company']}
        
        if customer_data.get('Address'):
            item['Address'] = {'S': customer_data['Address']}
        
        if customer_data.get('State'):
            item['State'] = {'S': customer_data['State']}
        
        if customer_data.get('PostalCode'):
            item['PostalCode'] = {'S': customer_data['PostalCode']}
        
        if customer_data.get('Phone'):
            item['Phone'] = {'S': customer_data['Phone']}
        
        if customer_data.get('Fax'):
            item['Fax'] = {'S': customer_data['Fax']}
        
        if customer_data.get('SupportRepId'):
            item['SupportRepId'] = {'N': str(customer_data['SupportRepId'])}
            if customer_data.get('RepFirstName') and customer_data.get('RepLastName'):
                item['SupportRepName'] = {'S': f"{customer_data['RepFirstName']} {customer_data['RepLastName']}"}
        
        # Calculate total spent
        total_spent = sum(
            float(order['invoice_data']['Total']) 
            for order in orders_data.values() 
            if order['invoice_data'].get('Total')
        )
        item['TotalSpent'] = {'N': str(Decimal(str(total_spent)))}
        
        return item
    
    def transform_customer_order(self, customer_id, order_data):
        """Transform customer order data to DynamoDB format"""
        invoice_data = order_data['invoice_data']
        line_items = order_data['line_items']
        
        item = {
            'PK': {'S': f"CUSTOMER#{customer_id}"},
            'SK': {'S': f"ORDER#{invoice_data['InvoiceDate']}#{invoice_data['InvoiceId']}"},
            'EntityType': {'S': 'Order'},
            'InvoiceId': {'N': str(invoice_data['InvoiceId'])},
            'InvoiceDate': {'S': invoice_data['InvoiceDate']},
            'Total': {'N': str(Decimal(str(invoice_data['Total'])))},
            'LineItemCount': {'N': str(len(line_items))}
        }
        
        # Optional billing fields
        if invoice_data.get('BillingAddress'):
            item['BillingAddress'] = {'S': invoice_data['BillingAddress']}
        
        if invoice_data.get('BillingCity'):
            item['BillingCity'] = {'S': invoice_data['BillingCity']}
        
        if invoice_data.get('BillingState'):
            item['BillingState'] = {'S': invoice_data['BillingState']}
        
        if invoice_data.get('BillingCountry'):
            item['BillingCountry'] = {'S': invoice_data['BillingCountry']}
        
        if invoice_data.get('BillingPostalCode'):
            item['BillingPostalCode'] = {'S': invoice_data['BillingPostalCode']}
        
        # Embed line items (if not too large)
        if len(line_items) <= 50:  # Limit to avoid item size issues
            line_items_list = []
            for line_item in line_items:
                line_item_data = {
                    'M': {
                        'InvoiceLineId': {'N': str(line_item['InvoiceLineId'])},
                        'TrackId': {'N': str(line_item['TrackId'])},
                        'UnitPrice': {'N': str(Decimal(str(line_item['UnitPrice'])))},
                        'Quantity': {'N': str(line_item['Quantity'])}
                    }
                }
                
                if line_item.get('TrackName'):
                    line_item_data['M']['TrackName'] = {'S': line_item['TrackName']}
                
                if line_item.get('ArtistName'):
                    line_item_data['M']['ArtistName'] = {'S': line_item['ArtistName']}
                
                if line_item.get('AlbumTitle'):
                    line_item_data['M']['AlbumTitle'] = {'S': line_item['AlbumTitle']}
                
                line_items_list.append(line_item_data)
            
            item['LineItems'] = {'L': line_items_list}
        
        return item
    
    def transform_playlist(self, playlist_data):
        """Transform playlist data to DynamoDB format"""
        playlist_info = playlist_data['playlist_info']
        tracks = playlist_data['tracks']
        
        item = {
            'PK': {'S': f"PLAYLIST#{playlist_info['PlaylistId']}"},
            'SK': {'S': 'METADATA'},
            'EntityType': {'S': 'Playlist'},
            'PlaylistId': {'N': str(playlist_info['PlaylistId'])},
            'Name': {'S': playlist_info['PlaylistName']},
            'TrackCount': {'N': str(len(tracks))}
        }
        
        # Calculate total duration
        total_duration = sum(
            track.get('Milliseconds', 0) or 0 
            for track in tracks
        )
        item['TotalDuration'] = {'N': str(total_duration)}
        
        # Embed tracks if playlist is not too large
        if len(tracks) <= 100:  # Limit to avoid item size issues
            tracks_list = []
            for track in tracks:
                track_data = {
                    'M': {
                        'TrackId': {'N': str(track['TrackId'])},
                        'Name': {'S': track['TrackName']}
                    }
                }
                
                if track.get('Milliseconds'):
                    track_data['M']['Duration'] = {'N': str(track['Milliseconds'])}
                
                if track.get('UnitPrice'):
                    track_data['M']['UnitPrice'] = {'N': str(Decimal(str(track['UnitPrice'])))}
                
                if track.get('ArtistName'):
                    track_data['M']['ArtistName'] = {'S': track['ArtistName']}
                
                if track.get('AlbumTitle'):
                    track_data['M']['AlbumTitle'] = {'S': track['AlbumTitle']}
                
                tracks_list.append(track_data)
            
            item['Tracks'] = {'L': tracks_list}
        else:
            # For large playlists, store track count only
            item['LargePlaylist'] = {'BOOL': True}
        
        return item
    
    def transform_employee(self, employee_data):
        """Transform employee data to DynamoDB format"""
        item = {
            'PK': {'S': f"EMPLOYEE#{employee_data['EmployeeId']}"},
            'SK': {'S': 'PROFILE'},
            'EntityType': {'S': 'Employee'},
            'EmployeeId': {'N': str(employee_data['EmployeeId'])},
            'FirstName': {'S': employee_data['FirstName']},
            'LastName': {'S': employee_data['LastName']},
            'Title': {'S': employee_data['Title']},
            'CustomerCount': {'N': str(employee_data.get('CustomerCount', 0))}
        }
        
        # Optional fields
        if employee_data.get('ReportsTo'):
            item['ReportsTo'] = {'N': str(employee_data['ReportsTo'])}
            if employee_data.get('ManagerFirstName') and employee_data.get('ManagerLastName'):
                item['ManagerName'] = {'S': f"{employee_data['ManagerFirstName']} {employee_data['ManagerLastName']}"}
        
        if employee_data.get('BirthDate'):
            item['BirthDate'] = {'S': employee_data['BirthDate']}
        
        if employee_data.get('HireDate'):
            item['HireDate'] = {'S': employee_data['HireDate']}
        
        if employee_data.get('Address'):
            item['Address'] = {'S': employee_data['Address']}
        
        if employee_data.get('City'):
            item['City'] = {'S': employee_data['City']}
        
        if employee_data.get('State'):
            item['State'] = {'S': employee_data['State']}
        
        if employee_data.get('Country'):
            item['Country'] = {'S': employee_data['Country']}
        
        if employee_data.get('PostalCode'):
            item['PostalCode'] = {'S': employee_data['PostalCode']}
        
        if employee_data.get('Phone'):
            item['Phone'] = {'S': employee_data['Phone']}
        
        if employee_data.get('Fax'):
            item['Fax'] = {'S': employee_data['Fax']}
        
        if employee_data.get('Email'):
            item['Email'] = {'S': employee_data['Email']}
        
        return item


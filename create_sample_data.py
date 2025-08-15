# create_sample_data.py
# Create sample data to demonstrate the interface

import sqlite3

# Create sample database
conn = sqlite3.connect("hansard_simple.db")

conn.execute("""
    CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY,
        year INTEGER,
        date TEXT,
        speaker TEXT,
        party TEXT,
        frame TEXT,
        quote TEXT,
        hansard_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hansard_url, speaker, quote)
    )
""")

# Sample quotes including your perfect example
sample_quotes = [
    {
        'year': 1905,
        'date': '02/05/1905',
        'speaker': 'Sir Kenelm Digby',
        'party': 'Conservative',
        'frame': 'LABOUR_NEED',
        'quote': 'If the immigrants, like the Huguenots of the seventeenth century, taught us new trades, new skill, then indeed we might welcome them, but the competition is against unskilled labour, which is the first to suffer from non-employment. We know that when the Board of Trade, in the Labour Gazette, shows that there are 2 or 3 per cent. of the members of a great trade union out of employment, it is of no importance whatever as compared with the number of unskilled labourers which are at the same time thrown out of employment. It is on the unskilled labour the want of employment falls heaviest and first, it is upon the unskilled labour, the casual labour, that this immigration produces the greatest mischief. It must be so; the immigrants come in to compete with our labourers and work at wages they could not earn in their own countries',
        'url': 'https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill'
    },
    {
        'year': 1905,
        'date': '02/05/1905', 
        'speaker': 'Mr. Hawkey',
        'party': 'Liberal',
        'frame': 'LABOUR_THREAT',
        'quote': 'The economic and industrial question is a matter of very great importance. Hon. Members opposite are apparently violently opposed to any legislation which will keep out competitive unskilled labour from this country. They would admit without hesitation an unlimited number of destitute aliens and let them loose upon our already over-congested unskilled labour market.',
        'url': 'https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill'
    },
    {
        'year': 1905,
        'date': '02/05/1905',
        'speaker': 'Sir Kenelm Digby', 
        'party': 'Conservative',
        'frame': 'RACIALISED',
        'quote': 'The right policy with regard to undesirable aliens is the policy of expulsion. We cannot blame the Australasians for their measures of restriction. Then as regards the diseased, the criminal, and the paupers, a nation cannot reasonably be called upon to pay the cost of hospitals, workhouses, and gaols for its neighbours to fill.',
        'url': 'https://api.parliament.uk/historic-hansard/commons/1905/may/02/aliens-bill'
    },
    {
        'year': 1906,
        'date': '15/03/1906',
        'speaker': 'Mr. Churchill',
        'party': 'Liberal', 
        'frame': 'MIXED',
        'quote': 'While we must acknowledge that alien immigration has brought certain benefits to our industrial development, we cannot ignore the legitimate concerns of British workers about wage competition. The question is not whether to exclude all foreign labour, but how to regulate it in the interests of both industrial progress and working-class welfare.',
        'url': 'https://api.parliament.uk/historic-hansard/commons/1906/mar/15/trade-disputes'
    },
    {
        'year': 1904,
        'date': '12/04/1904',
        'speaker': 'Mr. Balfour',
        'party': 'Conservative',
        'frame': 'LABOUR_NEED', 
        'quote': 'In certain industries, particularly those requiring specialized skills, the arrival of foreign craftsmen has filled gaps in our labour force that could not otherwise be met. The shipbuilding trades, for instance, have benefited considerably from the expertise brought by Continental workers.',
        'url': 'https://api.parliament.uk/historic-hansard/commons/1904/apr/12/shipbuilding-trades'
    }
]

# Insert sample data
for quote in sample_quotes:
    try:
        conn.execute("""
            INSERT OR IGNORE INTO quotes 
            (year, date, speaker, party, frame, quote, hansard_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            quote['year'], quote['date'], quote['speaker'], 
            quote['party'], quote['frame'], quote['quote'], quote['url']
        ))
    except Exception as e:
        print(f"Error inserting quote: {e}")

conn.commit()
conn.close()

print("Sample data created!")
print("Database: hansard_simple.db")
print("Launch with: streamlit run simple_explorer.py")
#!/usr/bin/env python3
"""
Insert player biographical data into DynamoDB.
Stores bios per season so class years stay accurate historically.

Usage:
    python3 insert_player_bios.py
"""

import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')


# =============================================================================
# 2024-25 IOWA HAWKEYES ROSTER
# =============================================================================
PLAYERS_2024_25 = [
    {
        "player_id": "4433815",
        "player_name": "Lucy Olsen",
        "jersey": "33",
        "position": "G",
        "height": "5-10",
        "hometown": "Collegeville, PA",
        "high_school": "Spring-Ford",
        "previous_school": "Villanova",
        "class_year": "Senior",
        "major": "Communications",
        "bio_summary": "A unanimous All-Big Ten first-team selection and 2025 WNBA Draft pick (#23, Washington Mystics), Olsen transferred from Villanova where she was an Honorable Mention All-American averaging 23.3 PPG. She eclipsed 2,000 career points as a Hawkeye and led Iowa with 573 points, becoming just the second Hawkeye since 2009 to record 30+ points, 5+ assists, and 5+ rebounds in a single game.",
        "accolades": [
            "2025 WNBA Draft Pick (#23, Washington Mystics)",
            "Unanimous All-Big Ten First Team (2024-25)",
            "Big Ten All-Tournament Team",
            "AP Honorable Mention All-American (2023-24)",
            "2021 Miss Pennsylvania Basketball",
            "2,000+ Career Points"
        ]
    },
    {
        "player_id": "4682968",
        "player_name": "Hannah Stuelke",
        "jersey": "45",
        "position": "F",
        "height": "6-2",
        "hometown": "Cedar Rapids, IA",
        "high_school": "Washington",
        "previous_school": "",
        "class_year": "Junior",
        "major": "English and Creative Writing",
        "bio_summary": "A Cedar Rapids native and the 44th Hawkeye to reach 1,000 career points, Stuelke is Iowa's most dominant post scorer. Her 47-point explosion against Penn State ranks third in program history. The 2023 Big Ten Sixth Player of the Year earned Second Team All-Big Ten honors and won the 2021 Nike Nationals Championship with All Iowa Attack.",
        "accolades": [
            "Second Team All-Big Ten (2023-24)",
            "Big Ten Sixth Player of the Year (2022-23)",
            "Iowa Gatorade Player of the Year",
            "Miss Iowa Basketball",
            "1,000+ Career Points"
        ]
    },
    {
        "player_id": "4433538",
        "player_name": "Addison O'Grady",
        "jersey": "44",
        "position": "F/C",
        "height": "6-4",
        "hometown": "Aurora, CO",
        "high_school": "Grandview",
        "previous_school": "",
        "class_year": "Senior",
        "major": "Chemical Engineering",
        "bio_summary": "A four-year Hawkeye and two-time state champion at Grandview High School, O'Grady brings size and efficiency to Iowa's frontcourt. She shot a career-high 64% from the floor in 2024-25 and tied for third in program history with a 7-of-7 shooting quarter against Drake. An Academic All-Big Ten honoree, she balances elite athletics with a demanding Chemical Engineering major.",
        "accolades": [
            "Academic All-Big Ten",
            "College Sports Communicators Academic All-District",
            "Big Ten Freshman of the Week (2022)",
            "2x Colorado State Champion"
        ]
    },
    {
        "player_id": "4898389",
        "player_name": "Sydney Affolter",
        "jersey": "3",
        "position": "G",
        "height": "5-11",
        "hometown": "Chicago, IL",
        "high_school": "Marist",
        "previous_school": "",
        "class_year": "Senior",
        "major": "",
        "bio_summary": "The ultimate glue player, Affolter earned All-Big Ten honorable mention and the Big Ten Sportsmanship Award in 2024-25. She recorded 8 career double-doubles and became the 11th Hawkeye since 2009 to grab 15+ rebounds in a single game. A key contributor on Iowa's 2024 Final Four run, she was named to the Big Ten All-Tournament Team and Albany Regional All-Tournament Team.",
        "accolades": [
            "All-Big Ten Honorable Mention (2024-25)",
            "Big Ten Sportsmanship Award (2024-25)",
            "Big Ten All-Tournament Team (2023-24)",
            "Albany Regional All-Tournament Team (2023-24)",
            "Academic All-Big Ten"
        ]
    },
    {
        "player_id": "4858677",
        "player_name": "Taylor McCabe",
        "jersey": "2",
        "position": "G",
        "height": "5-9",
        "hometown": "Fremont, NE",
        "high_school": "Fremont",
        "previous_school": "",
        "class_year": "Junior",
        "major": "Civil Engineering",
        "bio_summary": "Nebraska's all-time Class A 3-point record holder with 389 career threes, McCabe is one of the premier shooters in the Big Ten. She became the 21st Hawkeye to net 100 career three-pointers and is the second player since 2009 to shoot better than 40% from deep in three consecutive seasons. A multi-sport standout, she was also runner-up in the Nebraska Class A Cross Country State Championship.",
        "accolades": [
            "2022 Nebraska Gatorade Player of the Year",
            "Academic All-Big Ten",
            "Nebraska Class A 3-Point Record Holder (389)",
            "2022 Class A State Champion"
        ]
    },
    {
        "player_id": "4433985",
        "player_name": "Kylie Feuerbach",
        "jersey": "4",
        "position": "G",
        "height": "6-0",
        "hometown": "Sycamore, IL",
        "high_school": "Sycamore",
        "previous_school": "Iowa State",
        "class_year": "Graduate",
        "major": "Marketing",
        "bio_summary": "A transfer from Iowa State who has become a Hawkeye leader, Feuerbach hit the game-winning 3-pointer in the 2018 Nike EYBL Championship alongside teammate Caitlin Clark. She led Iowa with 43 steals in 2024-25 and brings veteran experience, defensive tenacity, and clutch shooting. A 2,000+ point scorer in high school, she earned Big 12 Freshman of the Week twice at Iowa State.",
        "accolades": [
            "Academic All-Big Ten",
            "Big 12 Freshman of the Week (2x at Iowa State)",
            "2018 Nike EYBL Champion",
            "First Team All-State (Illinois)",
            "2,000+ Career Points (High School)"
        ]
    },
    {
        "player_id": "5240175",
        "player_name": "Ava Heiden",
        "jersey": "5",
        "position": "C",
        "height": "6-4",
        "hometown": "Sherwood, OR",
        "high_school": "Sherwood",
        "previous_school": "",
        "class_year": "Freshman",
        "major": "Finance",
        "bio_summary": "The first Oregonian in Iowa women's basketball history, Heiden arrived as the No. 36 overall prospect and No. 5 post player nationally. She netted a career-high 15 points against Murray State in the NCAA Tournament and became the fifth Hawkeye freshman since 2009 to score 15+ points in an NCAA Tournament game.",
        "accolades": [
            "No. 36 Overall Prospect (ESPN)",
            "No. 5 Post Prospect (ESPN)",
            "6A Pacific Conference Player of the Year",
            "First Oregonian in Program History"
        ]
    },
    {
        "player_id": "5240176",
        "player_name": "Aaliyah Guyton",
        "jersey": "11",
        "position": "G",
        "height": "5-7",
        "hometown": "Peoria, IL",
        "high_school": "Peoria",
        "previous_school": "",
        "class_year": "Freshman",
        "major": "Sports and Recreation Management",
        "bio_summary": "Basketball royalty, Guyton's mother Adriana Mafra played 25 years for the Brazilian National Team and the Phoenix Mercury, while her father AJ Guyton played at Indiana and for the Chicago Bulls. The No. 57 overall prospect and No. 1 player in Illinois scored a career-high 15 points against Northwestern.",
        "accolades": [
            "No. 57 Overall Prospect (ESPN)",
            "No. 1 Player in Illinois (PrepGirlsHoop)",
            "2x First Team All-Big 12 Conference",
            "2x All-Big 12 Player of the Year"
        ],
        "notes": "Transferred to Illinois after 2024-25 season"
    },
    {
        "player_id": "5240178",
        "player_name": "Teagan Mallegni",
        "jersey": "55",
        "position": "G",
        "height": "6-1",
        "hometown": "McFarland, WI",
        "high_school": "McFarland",
        "previous_school": "",
        "class_year": "Freshman",
        "major": "Undecided",
        "bio_summary": "A versatile 6-1 guard who scored 14 points in her Iowa debut—the most by a true freshman since Caitlin Clark—Mallegni brings scoring punch and rebounding from the perimeter. The No. 64 overall prospect holds McFarland High School records for career points, single-season points, and single-game points (62).",
        "accolades": [
            "No. 64 Overall Prospect (ESPN)",
            "No. 2 Player in Wisconsin (PrepGirlsHoop)",
            "2x Wisconsin First Team All-State",
            "2x Rock Valley Player of the Year",
            "McFarland HS All-Time Leading Scorer"
        ]
    },
    {
        "player_id": "5240174",
        "player_name": "Taylor Stremlow",
        "jersey": "1",
        "position": "G",
        "height": "5-10",
        "hometown": "Verona, WI",
        "high_school": "Verona Area",
        "previous_school": "",
        "class_year": "Freshman",
        "major": "Business Marketing",
        "bio_summary": "The No. 88 overall prospect and Big 8 Conference Player of the Year, Stremlow is a stat-sheet stuffer who averaged double-digit points, rebounds, and near triple-double numbers in high school. She recorded five or more assists three times as a freshman—tying for sixth-most in a single season by a Hawkeye freshman since 2009.",
        "accolades": [
            "No. 88 Overall Prospect (ESPN)",
            "Big 8 Conference Player of the Year",
            "WBCA All-State First Team",
            "WBCA Academic All-State"
        ]
    },
    {
        "player_id": "4585713",
        "player_name": "AJ Ediger",
        "jersey": "34",
        "position": "F",
        "height": "6-2",
        "hometown": "Hudsonville, MI",
        "high_school": "Hamilton",
        "previous_school": "",
        "class_year": "Senior",
        "major": "",
        "bio_summary": "A four-year contributor and reliable post presence, Ediger provides depth and experience to Iowa's frontcourt. She shot a career-high 64% from the floor in 2024-25 while earning Academic All-Big Ten honors. The Michigan native brings leadership and defensive energy in her senior season.",
        "accolades": [
            "Academic All-Big Ten",
            "4-Year Letter Winner"
        ]
    },
    {
        "player_id": "4858658",
        "player_name": "Jada Gyamfi",
        "jersey": "23",
        "position": "F",
        "height": "6-1",
        "hometown": "Johnston, IA",
        "high_school": "Johnston",
        "previous_school": "",
        "class_year": "Junior",
        "major": "Elementary Education",
        "bio_summary": "Another proud Iowa native, Gyamfi helped Johnston win the 2022 Class 5A State Championship. A three-time Nike National Champion with All Iowa Attack, she comes from an athletic family—her sister Maya played at Northern Iowa, brother Chancelor was a First Team All-American in football, and her mother played basketball and golf at Mt. Mercy.",
        "accolades": [
            "2022 Class 5A Iowa State Champion",
            "3x Nike National Champion (All Iowa Attack)",
            "Iowa All-Tournament Team",
            "4x Academic All-Conference"
        ]
    },
    {
        "player_id": "5240177",
        "player_name": "Callie Levin",
        "jersey": "32",
        "position": "G",
        "height": "5-9",
        "hometown": "Solon, IA",
        "high_school": "Solon",
        "previous_school": "",
        "class_year": "Freshman",
        "major": "Business & Communication",
        "bio_summary": "Iowa's homegrown star, Levin was named 2024 Miss Iowa Basketball and USA TODAY Iowa Player of the Year after leading Solon to the 3A State Championship. She amassed nearly 2,000 career points in high school and won a Nike National Championship with All Iowa Attack.",
        "accolades": [
            "2024 Miss Iowa Basketball",
            "2024 USA TODAY Iowa Player of the Year",
            "2024 3A State Champion",
            "McDonald's All-America Nominee",
            "4x IBCA First Team All-State",
            "No. 1 Point Guard in Iowa (PrepGirlsHoop)"
        ]
    },
]


# =============================================================================
# 2025-26 IOWA HAWKEYES ROSTER
# =============================================================================
PLAYERS_2025_26 = [
    {
        "player_id": "4682968",
        "player_name": "Hannah Stuelke",
        "jersey": "45",
        "position": "F",
        "height": "6-2",
        "hometown": "Cedar Rapids, IA",
        "high_school": "Washington",
        "previous_school": "",
        "class_year": "Senior",
        "major": "English and Creative Writing",
        "bio_summary": "A Cedar Rapids native and the 44th Hawkeye to reach 1,000 career points, Stuelke enters her senior year on the Naismith Trophy Preseason Watch List. Her 47-point explosion against Penn State ranks third in program history. The two-time Second Team All-Big Ten selection and 2023 Big Ten Sixth Player of the Year is poised for a dominant final season.",
        "accolades": [
            "Preseason First Team All-Big Ten (2025-26)",
            "Naismith Trophy Preseason Watch List",
            "Katrina McClain Award Preseason Watch List",
            "Second Team All-Big Ten (2x)",
            "Big Ten Sixth Player of the Year (2022-23)",
            "Miss Iowa Basketball",
            "1,000+ Career Points"
        ]
    },
    {
        "player_id": "5240175",
        "player_name": "Ava Heiden",
        "jersey": "5",
        "position": "C",
        "height": "6-4",
        "hometown": "Sherwood, OR",
        "high_school": "Sherwood",
        "previous_school": "",
        "class_year": "Sophomore",
        "major": "Finance",
        "bio_summary": "The first Oregonian in Iowa women's basketball history, Heiden exploded onto the scene as a sophomore, earning Big Ten Player of the Week and USBWA National Player of the Week honors after a 21-point, 14-rebound performance. She shot 65.7% from the field and is emerging as one of the most dominant post players in the conference.",
        "accolades": [
            "Big Ten Player of the Week (Nov. 2025)",
            "USBWA National Player of the Week (Nov. 2025)",
            "No. 36 Overall Prospect (ESPN)",
            "No. 5 Post Prospect (ESPN)",
            "First Oregonian in Program History"
        ]
    },
    {
        "player_id": "4858677",
        "player_name": "Taylor McCabe",
        "jersey": "2",
        "position": "G",
        "height": "5-9",
        "hometown": "Fremont, NE",
        "high_school": "Fremont",
        "previous_school": "",
        "class_year": "Senior",
        "major": "Civil Engineering",
        "bio_summary": "Nebraska's all-time Class A 3-point record holder with 389 career threes, McCabe is one of the premier shooters in the Big Ten. The 21st Hawkeye to net 100 career three-pointers, she is the second player since 2009 to shoot better than 40% from deep in three consecutive seasons. An Academic All-Big Ten honoree studying Civil Engineering.",
        "accolades": [
            "2022 Nebraska Gatorade Player of the Year",
            "Academic All-Big Ten",
            "Nebraska Class A 3-Point Record Holder (389)",
            "100+ Career 3-Pointers at Iowa"
        ]
    },
    {
        "player_id": "4433985",
        "player_name": "Kylie Feuerbach",
        "jersey": "4",
        "position": "G",
        "height": "6-0",
        "hometown": "Sycamore, IL",
        "high_school": "Sycamore",
        "previous_school": "Iowa State",
        "class_year": "Graduate",
        "major": "Marketing",
        "bio_summary": "A fifth-year veteran and Hawkeye leader, Feuerbach returns for her final season after leading Iowa with 43 steals in 2024-25. She hit the game-winning 3-pointer in the 2018 Nike EYBL Championship alongside Caitlin Clark and brings invaluable experience, defensive intensity, and clutch shooting to this young roster.",
        "accolades": [
            "Academic All-Big Ten",
            "Team Leader in Steals (2024-25)",
            "2018 Nike EYBL Champion",
            "Big 12 Freshman of the Week (2x at Iowa State)"
        ]
    },
    {
        "player_id": "5240174",
        "player_name": "Taylor Stremlow",
        "jersey": "1",
        "position": "G",
        "height": "5-10",
        "hometown": "Verona, WI",
        "high_school": "Verona Area",
        "previous_school": "",
        "class_year": "Sophomore",
        "major": "Business Marketing",
        "bio_summary": "Building on a strong freshman campaign, Stremlow recorded a career-high 10 points in the NCAA Tournament and made her first career start against Rhode Island. The Big 8 Conference Player of the Year tied for sixth-most games with 5+ assists by a Hawkeye freshman since 2009.",
        "accolades": [
            "No. 88 Overall Prospect (ESPN)",
            "Big 8 Conference Player of the Year",
            "WBCA All-State First Team",
            "WBCA Academic All-State"
        ]
    },
    {
        "player_id": "5240178",
        "player_name": "Teagan Mallegni",
        "jersey": "55",
        "position": "G",
        "height": "6-1",
        "hometown": "McFarland, WI",
        "high_school": "McFarland",
        "previous_school": "",
        "class_year": "Sophomore",
        "major": "Undecided",
        "bio_summary": "A versatile 6-1 guard who scored 14 points in her Iowa debut—the most by a true freshman since Caitlin Clark—Mallegni brings scoring punch and rebounding from the perimeter. The McFarland HS all-time leading scorer saw action in 30 games as a freshman, totaling 97 points and 64 rebounds.",
        "accolades": [
            "No. 64 Overall Prospect (ESPN)",
            "No. 2 Player in Wisconsin (PrepGirlsHoop)",
            "2x Wisconsin First Team All-State",
            "McFarland HS All-Time Leading Scorer"
        ]
    },
    {
        "player_id": "5240177",
        "player_name": "Callie Levin",
        "jersey": "32",
        "position": "G",
        "height": "5-9",
        "hometown": "Solon, IA",
        "high_school": "Solon",
        "previous_school": "",
        "class_year": "Sophomore",
        "major": "Business & Communication",
        "bio_summary": "Iowa's homegrown star returns after scoring her first career points in the NCAA Tournament. The 2024 Miss Iowa Basketball and USA TODAY Iowa Player of the Year led Solon to the 3A State Championship and won a Nike National Championship with All Iowa Attack.",
        "accolades": [
            "2024 Miss Iowa Basketball",
            "2024 USA TODAY Iowa Player of the Year",
            "2024 3A State Champion",
            "McDonald's All-America Nominee",
            "No. 1 Point Guard in Iowa (PrepGirlsHoop)"
        ]
    },
    {
        "player_id": "4858658",
        "player_name": "Jada Gyamfi",
        "jersey": "23",
        "position": "F",
        "height": "6-1",
        "hometown": "Johnston, IA",
        "high_school": "Johnston",
        "previous_school": "",
        "class_year": "Senior",
        "major": "Elementary Education",
        "bio_summary": "A proud Iowa native entering her senior season, Gyamfi helped Johnston win the 2022 Class 5A State Championship. A three-time Nike National Champion with All Iowa Attack, she comes from an athletic family and brings energy, rebounding, and leadership to Iowa's frontcourt.",
        "accolades": [
            "2022 Class 5A Iowa State Champion",
            "3x Nike National Champion (All Iowa Attack)",
            "Iowa All-Tournament Team",
            "4x Academic All-Conference"
        ]
    },
    {
        "player_id": "5175682",
        "player_name": "Kennise Johnson",
        "jersey": "13",
        "position": "G",
        "height": "5-4",
        "hometown": "Joliet, IL",
        "high_school": "Example Academy",
        "previous_school": "",
        "class_year": "Junior",
        "major": "Sport and Recreation Management",
        "bio_summary": "A speedy guard from Joliet, Illinois, Johnson won a Prep School National Championship in her junior year of high school. The No. 3 guard and No. 13 overall prospect in Illinois averaged 11.3 points, 6.2 assists, 5.9 rebounds, and 3.1 steals per game, showcasing her all-around floor game.",
        "accolades": [
            "Prep School National Champion",
            "No. 3 Guard in Illinois",
            "No. 13 Overall Prospect in Illinois"
        ]
    },
    {
        "player_id": "5238283",
        "player_name": "Chazadi Wright",
        "jersey": "11",
        "position": "G",
        "height": "5-4",
        "hometown": "Atlanta, GA",
        "high_school": "Wesleyan School",
        "previous_school": "Georgia Tech",
        "class_year": "Sophomore",
        "major": "Business Administration",
        "bio_summary": "A dynamic transfer from Georgia Tech, Wright (nicknamed 'Chit-Chat') appeared in all 33 games with 12 starts as a freshman. The four-star recruit scored a career-high 16 points against Pittsburgh and ranked second on the team in assists. A two-time Georgia all-state honoree who also won a track state championship.",
        "accolades": [
            "Four-Star Recruit (ESPN)",
            "Region 7 Class 3A Player of the Year",
            "2x Georgia All-State",
            "Track State Champion",
            "1,000+ Career Points (High School)"
        ]
    },
    {
        "player_id": "5239475",
        "player_name": "Emely Rodriguez",
        "jersey": "21",
        "position": "G/F",
        "height": "6-0",
        "hometown": "La Romana, Dominican Republic",
        "high_school": "Central Pointe Academy",
        "previous_school": "UCF",
        "class_year": "Sophomore",
        "major": "Criminal Justice",
        "bio_summary": "A talented transfer from UCF where she earned All-Big 12 Freshman Team honors, Rodriguez brings international flair from the Dominican Republic. She averaged 11.9 points and 5.3 rebounds as a freshman, posting 16 double-figure scoring games. The Miami-Dade County Player of the Year led her high school to the SIAA State Championship.",
        "accolades": [
            "All-Big 12 Freshman Team (2024-25)",
            "Miami-Dade County Player of the Year",
            "SIAA State Champion",
            "Career-High 21 Points vs Iowa State"
        ]
    },
    {
        "player_id": "5311543",
        "player_name": "Addie Deal",
        "jersey": "7",
        "position": "G",
        "height": "6-0",
        "hometown": "Irvine, CA",
        "high_school": "Mater Dei",
        "previous_school": "",
        "class_year": "Freshman",
        "major": "Business",
        "bio_summary": "The crown jewel of Iowa's 2025 recruiting class, Deal is a five-star prospect ranked No. 18 overall nationally and No. 2 in California. A Wooden Award Watch List selection, she attended USA Basketball minicamps and won the Section 7 3-Point Contest. Her brother plays at Grinnell College alongside Lisa Bluder's son.",
        "accolades": [
            "Wooden Award Watch List",
            "No. 18 Overall Prospect (ESPN)",
            "Five-Star Recruit",
            "No. 2 Player in California",
            "USA Basketball Minicamp Participant",
            "Section 7 3-Point Contest Champion"
        ]
    },
    {
        "player_id": "5311544",
        "player_name": "Journey Houston",
        "jersey": "8",
        "position": "G",
        "height": "6-0",
        "hometown": "Davenport, IA",
        "high_school": "North",
        "previous_school": "",
        "class_year": "Freshman",
        "major": "Sports & Recreation Management",
        "bio_summary": "A Davenport native and four-star prospect, Houston was rated as high as No. 19 nationally and a five-star recruit before a season-ending injury her junior year. She recorded 1,000 points and 500 rebounds in just two and a half seasons and led her team to the 2023 Nike EYBL National Runner-Up finish. Both parents were college athletes.",
        "accolades": [
            "No. 85 Overall Prospect (ESPN)",
            "Four-Star Recruit",
            "2023 Nike EYBL National Runner-Up",
            "1,000+ Points in 2.5 Seasons"
        ]
    },
    {
        "player_id": "5311545",
        "player_name": "Layla Hays",
        "jersey": "12",
        "position": "C",
        "height": "6-5",
        "hometown": "Wasilla, AK",
        "high_school": "Wasilla",
        "previous_school": "",
        "class_year": "Freshman",
        "major": "Sport & Recreation Management",
        "bio_summary": "The first Alaskan in Iowa women's basketball history, Hays is a four-star prospect ranked No. 70 overall and No. 1 in Alaska. The 6-5 center averaged 16.2 points, 11.9 rebounds, and 2.0 blocks as a junior while winning her first state title. Her mom's best friend Leah Magner played for the Hawkeyes from 1998-2002.",
        "accolades": [
            "No. 70 Overall Prospect (ESPN)",
            "Four-Star Recruit",
            "No. 1 Player in Alaska",
            "Alaska State Champion",
            "4x First Team All-Region",
            "First Alaskan in Program History"
        ]
    },
]


def insert_player_bios(players: list, season_year: int):
    """Insert player bios into DynamoDB with season-specific SK."""
    season_label = f"{season_year - 1}-{str(season_year)[2:]}"
    print(f"\nInserting {len(players)} player bios for {season_label} season...\n")
    
    for player in players:
        item = {
            'pk': f"PLAYER#{player['player_id']}",
            'sk': f"BIO#{season_year}",
            'entity_type': 'PLAYER_BIO',
            'player_id': player['player_id'],
            'player_name': player['player_name'],
            'jersey': player['jersey'],
            'position': player['position'],
            'height': player['height'],
            'hometown': player['hometown'],
            'high_school': player['high_school'],
            'previous_school': player.get('previous_school', ''),
            'class_year': player['class_year'],
            'major': player.get('major', ''),
            'bio_summary': player['bio_summary'],
            'accolades': player.get('accolades', []),
            'notes': player.get('notes', ''),
            'season': season_year,
            'inserted_at': datetime.now().isoformat()
        }
        
        table.put_item(Item=item)
        print(f"  ✅ {player['player_name']} (#{player['jersey']}) - {player['class_year']}")
    
    print(f"\n✅ Inserted {len(players)} player bios for {season_label}!")


def main():
    print("=" * 60)
    print("CourtVision AI - Player Bio Import")
    print("=" * 60)
    
    # Insert 2024-25 season bios
    insert_player_bios(PLAYERS_2024_25, 2025)
    
    # Insert 2025-26 season bios
    insert_player_bios(PLAYERS_2025_26, 2026)
    
    print("\n" + "=" * 60)
    print("Import complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
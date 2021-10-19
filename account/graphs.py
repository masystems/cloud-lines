from json import dumps

def get_graphs():
    return dumps({
        "g1": {
            "id": "total_added",
            "title": "Total Animals in Database",
            "desc": "The total number of pedigrees in the database over the last ten years"
        },
        "g2": {
            "id": "registered",
            "title": "Animals Registered Per Year",
            "desc": "The number of pedigrees registered each year for the last ten years"
        },
        "g3": {
            "id": "current_alive",
            "title": "Number of Living Animals by Sex",
            "desc": "The current number of living males and females"
        },
        "g4": {
            "id": "born",
            "title": "Animals Born Per Year",
            "desc": "The number of pedigrees born each year for the last ten years"
        },
    })
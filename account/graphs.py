from json import dumps

def get_graphs():
    return dumps({
        "g1": {
            "id": "total_added",
            "title": "Total Pedigrees Added",
            "desc": "The total number of pedigrees in the database over the last ten years"
        },
        "g2": {
            "id": "registered",
            "title": "Pedigrees Registered",
            "desc": "The number of pedigrees registered each year for the last ten years"
        },
        "g3": {
            "id": "current_alive",
            "title": "Current Pedigrees Alive",
            "desc": "The current number of living males and females"
        },
    })
from json import dumps

def get_graphs():
    return dumps({
        "g1": {"id": "total_line", "title": "Total Pedigrees History", "selected": False}, 
        "g2": {"id": "total_bar", "title": "Total Pedigrees", "selected": False}, 
        "g3": {"id": "living_bar", "title": "Total Pedigrees Alive", "selected": False},
    })
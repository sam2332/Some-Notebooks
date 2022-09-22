from collections import defaultdict

class ScoreSort():
    def __init__(self,sorter):
        self.sorter = sorter
        
    def sort(self,data):
        index = defaultdict(list)
        for item in data:
            result = self.sorter(item)
            index[result].append(item)
        return_data = []
        for score in sorted(index.keys(),reverse=True):
            return_data.append(index[score])
        return return_data

'''        
def item_ranker(item):
    if item['name'] == 'sam':
        return 5
    
    if item['name'] == 'jim':
        return 0
    
    if item['name'] == 'kim':
        return 10
    
    return 1
s = ScoreSort(item_ranker)
s.sort([
    {'name':'jim'},
    {'name':'sam'},
    {'name':'ryan'},
    {'name':'sam'},
    {'name':'kim'},
    {'name':'larry'}
])
>[{'name': 'kim'},
> {'name': 'sam'},
> {'name': 'sam'},
> {'name': 'ryan'},
> {'name': 'larry'},
> {'name': 'jim'}]
'''
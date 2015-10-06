from uszipcode import ZipcodeSearchEngine

search = ZipcodeSearchEngine()
res = search.by_population(lower=5000,upper=10000)
print(len(res))
print(res[0])

for zipcode in res:
    print(zipcode.Zipcode)
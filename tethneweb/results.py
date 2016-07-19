from itertools import count


def Result(request, result_class=dict):
    return result_class(request.client, request.get())


class ResultList(object):
    limit = 20

    def __init__(self, request, result_class=dict):
        self.request = request
        self.result_class = result_class
        self.cache = {}

    def _stop(self, offset, limit, c, step):
        return offset + limit > c or (step and offset + step > c)

    def _result(self, data):
        return self.result_class(self.request.client, data)

    def __getitem__(self, key):
        if isinstance(key, slice):
            xargs = []
            start = key.start if key.start else 0
            if start < 0:
                raise IndexError('Negative indices are not supported')
            xargs.append(start)
            if key.stop:
                iterator_class = xrange
                if key.stop < 0:
                    raise IndexError('Negative indices are not supported')
                xargs.append(key.stop)
                if key.step:
                    limit = 1
                    xargs.append(key.step)
                else:
                    limit = self.limit
                    xargs.append(limit)
            else:
                iterator_class = count
                limit = self.limit
                xargs.append(limit)

            s = 0           # Current number of results.
            results = []    # Each result is a dict from JSON data.
            c = None        # 'count' value populated from first response.
            for offset in iterator_class(*xargs):
                request = self.request.clone()    # Copies params and headers.
                request.set_param('offset', offset)
                request.set_param('limit', limit)
                response = request.get()
                results += response['results']
                c = response['count']
                if len(results) - s == 0 or self._stop(offset, limit, c, key.step):
                    break

                s = len(results)
            return [self._result(result) for result in results]

        elif isinstance(key, int):
            if key in self.cache:
                return self.cache[key]

            if int < 0:
                raise IndexError('Negative indices are not supported')
            request = self.request.clone()
            request.set_param('offset', key)
            request.set_param('limit', 1)
            results = request.get()['results']
            if len(results) == 0:
                raise IndexError('Index %i beyond end of results' % key)
            self.cache[key] = self._result(results[0])
            return self.cache[key]
        raise TypeError('')

import sky_mitm.more_like_this.limit_more_like_this_recs as mod
from sky_mitm import FakeFlow, FakeRequest, FakeJsonResponse

recommendations = [1, 2, 3, 4, 5, 6]

# Test when url matches the filter

mod.set_arguments(limit=2,
                  pattern='123456')

test_flow = FakeFlow(FakeRequest(url='https://qxvp.skyq.sky.com/content/123456/more-like-this'),
                     FakeJsonResponse(content={"recommendations": recommendations}))

mod.response(test_flow)
content = test_flow.response.dict()
assert len(content.get('recommendations', [])) == mod.LIMIT

# Test when URL does not match filter
test_flow = FakeFlow(FakeRequest(url='https://qxvp.skyq.sky.com/content/54321/more-like-this'),
                     FakeJsonResponse(content={"recommendations": recommendations}
                                      ))
mod.response(test_flow)
content = test_flow.response.dict()
assert len(content.get('recommendations', [])) == len(recommendations)

# Test when no filter provided
mod.set_arguments(limit=2,
                  pattern='')

test_flow = FakeFlow(FakeRequest(url='https://qxvp.skyq.sky.com/content/54321/more-like-this'),
                     FakeJsonResponse(content={"recommendations": recommendations}
                                      ))
mod.response(test_flow)
content = test_flow.response.dict()
assert len(content.get('recommendations', [])) == mod.LIMIT


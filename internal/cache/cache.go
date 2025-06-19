package cache

type Cache interface {
	GetCacheVal(key string) (any, error)
	SetCacheVal(key string, val any) error
	DelCacheVal(key string) error
}

type DummyCache struct {}

func (c *DummyCache) GetCacheVal(key string) (any, error) {
	return nil, nil
}

func (c *DummyCache) SetCacheVal(key string, val any) error {
	return nil
}

func (c *DummyCache) DelCacheVal(key string) error {
	return nil
}

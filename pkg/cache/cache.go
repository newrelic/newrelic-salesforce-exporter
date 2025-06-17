package cache

type Cache interface {
	GetCacheVal(key string) (any, error)
	SetCacheVal(key string, val any) error
	DelCacheVal(key string) error
}

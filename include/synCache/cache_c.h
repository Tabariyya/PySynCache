#pragma once

#ifdef __cplusplus
extern "C" {
#endif
#include <stddef.h>
#include <stdint.h>

/* Initialize the singleton Cache. Call once before any other cache_* function. */
void cache_init(
    const char *broker_auth_token,
    long max_no_of_entries
);

/* Set string value */
void cache_set_string(
    const char *name_space,
    const char *id,
    const char *value,
    const long *ttl /* nullable */
);

/* Set raw binary value */
void cache_set_raw(
    const char *name_space,
    const char *id,
    const uint8_t *value,
    size_t value_size,
    const long *ttl /* nullable */
);

/* Get raw value
 * - buffer is allocated by the function, size written to *out_size
 * - caller must free it with cache_free()
 */
uint8_t *cache_get_raw(
    const char *name_space,
    const char *id,
    size_t *out_size
);

/* Get string value
 * - string is null-terminated
 * - caller must free it with cache_free()
 */
char *cache_get_string(
    const char *name_space,
    const char *id
);

/* Eviction */
void cache_evict(
    const char *name_space,
    const char *id
);

void cache_evict_all(void);

void cache_evict_all_namespace(const char *name_space);

/* Free memory returned by get functions */
void cache_free(void *ptr);

#ifdef __cplusplus
}
#endif

#pragma once

#ifdef __cplusplus
extern "C" {
#endif
#include <stddef.h>
#include <stdint.h>

/* Opaque handle to the C++ Controller */
typedef struct controller_handle controller_handle_t;

/* Create / destroy */
controller_handle_t *controller_create(
    const char *broker_auth_token,
    long max_no_of_entries
);

void controller_destroy(controller_handle_t *handle);

/* Set string value */
void controller_set_string(
    controller_handle_t *handle,
    const char *name_space,
    const char *id,
    const char *value,
    const long *ttl /* nullable */
);

/* Set raw binary value */
void controller_set_raw(
    controller_handle_t *handle,
    const char *name_space,
    const char *id,
    const uint8_t *value,
    size_t value_size,
    const long *ttl /* nullable */
);

/* Get raw value
 * - buffer is allocated by the function, size written to *out_size
 * - caller must free it with controller_free()
 */
uint8_t *controller_get_raw(
    const controller_handle_t *handle,
    const char *name_space,
    const char *id,
    size_t *out_size
);

/* Get string value
 * - string is null-terminated
 * - caller must free it with controller_free()
 */
char *controller_get_string(
    const controller_handle_t *handle,
    const char *name_space,
    const char *id
);

/* Eviction */
void controller_evict(
    controller_handle_t *handle,
    const char *name_space,
    const char *id
);

void controller_evict_all(controller_handle_t *handle);

void controller_evict_all_namespace(controller_handle_t *handle, const char *name_space);

/* Free memory returned by get functions */
void controller_free(void *ptr);

#ifdef __cplusplus
}
#endif

<script setup lang="ts">
import { NIcon, NBreadcrumbItem, NFlex } from 'naive-ui'
import { ReleaseIcon } from '../icons'
import { Release } from '../../models';

defineProps<{
    release?: Release;
}>();
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="#">
            <n-icon>
                <ReleaseIcon />
            </n-icon>
            {{ release?.toString() ?? "Unknown" }}
        </router-link>
    </n-breadcrumb-item>
</template>
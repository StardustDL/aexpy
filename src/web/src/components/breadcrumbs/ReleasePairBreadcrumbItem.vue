<script setup lang="ts">
import { NIcon, NBreadcrumbItem, NFlex } from 'naive-ui'
import { ReleaseIcon } from '../icons'
import { ReleasePair } from '../../models';

defineProps<{
    release?: ReleasePair;
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
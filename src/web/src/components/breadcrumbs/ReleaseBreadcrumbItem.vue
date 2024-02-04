<script setup lang="ts">
import { NIcon, NBreadcrumbItem, NSpace } from 'naive-ui'
import { ReleaseIcon } from '../icons'
import { Release } from '../../models';

defineProps<{
    release?: Release;
}>();
</script>

<template>
    <n-breadcrumb-item>
        <n-space>
            <n-icon>
                <ReleaseIcon />
            </n-icon>
            {{ release?.toString() ?? "Unknown" }}
        </n-space>
    </n-breadcrumb-item>
</template>
<script setup lang="ts">
import { NIcon, NBreadcrumbItem, NFlex } from 'naive-ui'
import { PackageIcon, VersionIcon } from '../icons'
import { Release } from '../../models';

defineProps<{
    release?: Release;
}>();
</script>

<template>
    <n-breadcrumb-item v-if="release">
        <router-link :to="`/packages/${release.project}`">
            <n-icon :component="PackageIcon" />
            {{ release.project }}
        </router-link>
    </n-breadcrumb-item>
    <n-breadcrumb-item>
        <router-link to="#">
            <n-icon :component="VersionIcon" />
            {{ release?.version ?? "Unknown" }}
        </router-link>
    </n-breadcrumb-item>
</template>
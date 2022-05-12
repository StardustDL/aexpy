<script setup lang="ts">
import { NButton, NIcon, NResult } from 'naive-ui'
import { AlertCircle } from '@vicons/tabler'
import { HomeIcon } from '../components/icons'
import { RouterLink, useRoute } from 'vue-router'
import { useStore } from '../services/store'
import NotFound from '../components/NotFound.vue'

const store = useStore();
const route = useRoute();

const params = <{
    path: string[]
}>route.params;

document.title = `Not Found - AexPy`;

</script>

<template>
    <NotFound :path="params.path.join('/')" />
</template>
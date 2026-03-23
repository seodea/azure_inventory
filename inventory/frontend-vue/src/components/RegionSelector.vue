<template>
  <div style="margin: 20px 0">
    <label>리전 선택: </label>
  <select :value="modelValue" @change="onChange">
      <option value="">리전을 선택하세요</option>
      <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
    </select>
  </div>
</template>

<script setup>

const props = defineProps({
  regions: Array,
  modelValue: String
});
const emit = defineEmits(['update:modelValue']);

function onChange(event) {
  emit('update:modelValue', event.target.value);
}
</script>

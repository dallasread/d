import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import DNS from './DNS.vue';
import { useDNSStore } from '../stores/dns';
import { useAppStore } from '../stores/app';

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

describe('DNS Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('renders empty state when no domain is set', () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    expect(wrapper.text()).toContain('Enter a domain to view DNS records');
  });

  it('renders loading state', () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.loading = true;

    expect(wrapper.text()).toContain('DNS Records');
  });

  it('displays DNS records when available', async () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.aRecords = {
      records: [
        {
          name: 'example.com.',
          record_type: 'A',
          value: '93.184.216.34',
          ttl: 3600,
        },
      ],
      query_time: 0.123,
      resolver: 'system',
      raw_output: null,
    };

    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('93.184.216.34');
    expect(wrapper.text()).toContain('example.com');
  });

  it('displays multiple record types', async () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.aRecords = {
      records: [
        {
          name: 'example.com.',
          record_type: 'A',
          value: '93.184.216.34',
          ttl: 3600,
        },
      ],
      query_time: 0.123,
      resolver: 'system',
      raw_output: null,
    };

    dnsStore.mxRecords = {
      records: [
        {
          name: 'example.com.',
          record_type: 'MX',
          value: '10 mail.example.com.',
          ttl: 3600,
        },
      ],
      query_time: 0.145,
      resolver: 'system',
      raw_output: null,
    };

    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('93.184.216.34');
    expect(wrapper.text()).toContain('mail.example.com');
  });

  it('displays error state', async () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.error = 'DNS query failed';

    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Error');
    expect(wrapper.text()).toContain('DNS query failed');
  });

  it('shows diagnostic issues for missing A/AAAA records', async () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.aRecords = {
      records: [],
      query_time: 0.123,
      resolver: 'system',
      raw_output: null,
    };
    dnsStore.aaaaRecords = {
      records: [],
      query_time: 0.134,
      resolver: 'system',
      raw_output: null,
    };

    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('No A or AAAA records found');
  });

  it('shows diagnostic warning for single nameserver', async () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.nsRecords = {
      records: [
        {
          name: 'example.com.',
          record_type: 'NS',
          value: 'ns1.example.com.',
          ttl: 86400,
        },
      ],
      query_time: 0.145,
      resolver: 'system',
      raw_output: null,
    };

    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Only 1 nameserver configured');
  });

  it('shows success for multiple nameservers', async () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.nsRecords = {
      records: [
        {
          name: 'example.com.',
          record_type: 'NS',
          value: 'ns1.example.com.',
          ttl: 86400,
        },
        {
          name: 'example.com.',
          record_type: 'NS',
          value: 'ns2.example.com.',
          ttl: 86400,
        },
      ],
      query_time: 0.145,
      resolver: 'system',
      raw_output: null,
    };

    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('nameservers configured (good redundancy)');
  });

  it('displays MX record with priority', async () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.mxRecords = {
      records: [
        {
          name: 'example.com.',
          record_type: 'MX',
          value: '10 mail.example.com.',
          ttl: 3600,
        },
      ],
      query_time: 0.145,
      resolver: 'system',
      raw_output: null,
    };

    await wrapper.vm.$nextTick();

    // Should show priority and hostname separately
    expect(wrapper.text()).toContain('10');
    expect(wrapper.text()).toContain('mail.example.com');
  });

  it('shows warning when no MX records', async () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.mxRecords = {
      records: [],
      query_time: 0.145,
      resolver: 'system',
      raw_output: null,
    };

    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('No MX records');
  });

  it('displays correct record count', async () => {
    const wrapper = mount(DNS, {
      global: {
        plugins: [createPinia()],
      },
    });

    const appStore = useAppStore();
    const dnsStore = useDNSStore();

    appStore.domain = 'example.com';
    dnsStore.aRecords = {
      records: [
        {
          name: 'example.com.',
          record_type: 'A',
          value: '93.184.216.34',
          ttl: 3600,
        },
        {
          name: 'example.com.',
          record_type: 'A',
          value: '93.184.216.35',
          ttl: 3600,
        },
      ],
      query_time: 0.123,
      resolver: 'system',
      raw_output: null,
    };

    await wrapper.vm.$nextTick();

    // Should show count of 2
    expect(wrapper.html()).toContain('2');
  });
});

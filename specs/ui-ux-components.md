# AI Knowledge Base - UI/UX Components Specification

## Design System Integration

### Battalion Platform Alignment
- **Color Scheme**: Battalion's energy sector palette
  - Primary: `#0F172A` (Deep Navy)
  - Secondary: `#3B82F6` (Electric Blue)
  - Accent: `#10B981` (Energy Green)
  - Warning: `#F59E0B` (Alert Amber)
  - Error: `#EF4444` (Critical Red)
  - Background: `#F8FAFC` (Light) / `#0F172A` (Dark)

- **Typography**: Inter font family
  - Headers: 600-800 weight
  - Body: 400-500 weight
  - Monospace: JetBrains Mono for code

- **Spacing**: 8px base unit system
- **Border Radius**: 4px, 8px, 12px, 16px
- **Shadows**: Battalion's elevation system

## Component Library

### 1. Layout Components

#### AppShell
```tsx
interface AppShellProps {
  sidebar: ReactNode
  header: ReactNode
  footer?: ReactNode
  children: ReactNode
  notifications?: NotificationProps[]
}

// Features:
- Responsive sidebar (collapsible on mobile)
- Fixed header with search
- Notification center
- Breadcrumb navigation
- Dark/light mode toggle
```

#### NavigationSidebar
```tsx
interface NavigationItem {
  icon: IconType
  label: string
  href: string
  badge?: string | number
  children?: NavigationItem[]
}

// Features:
- Nested navigation support
- Active state indication
- Keyboard navigation
- Search filter
- Quick actions section
```

### 2. Search Components

#### SearchBar
```tsx
interface SearchBarProps {
  placeholder?: string
  suggestions?: boolean
  filters?: FilterOption[]
  onSearch: (query: string) => void
  recentSearches?: string[]
}

// Features:
- Auto-complete suggestions
- Voice search support
- Search history dropdown
- Filter chips
- Loading state
```

#### AdvancedSearchPanel
```tsx
interface AdvancedSearchProps {
  documentTypes: DocumentType[]
  dateRanges: DateRange[]
  sources: DataSource[]
  onSearch: (params: SearchParams) => void
}

// Features:
- Multi-select filters
- Date range picker
- Source selection
- Search templates
- Save search criteria
```

#### SearchResults
```tsx
interface SearchResultsProps {
  results: SearchResult[]
  loading: boolean
  totalCount: number
  onLoadMore: () => void
  viewMode: 'list' | 'grid' | 'compact'
}

// Features:
- Result highlighting
- Relevance scoring display
- Quick preview on hover
- Bulk selection
- Export options
```

### 3. Document Components

#### DocumentViewer
```tsx
interface DocumentViewerProps {
  document: Document
  highlights?: TextHighlight[]
  annotations?: Annotation[]
  onAnnotate: (annotation: Annotation) => void
  tools?: ViewerTool[]
}

// Features:
- PDF/Word/Excel rendering
- Text highlighting
- Annotation tools
- Zoom controls
- Full-screen mode
- Print support
```

#### DocumentCard
```tsx
interface DocumentCardProps {
  document: Document
  variant: 'compact' | 'detailed' | 'preview'
  actions?: DocumentAction[]
  onClick?: () => void
}

// Features:
- Document type icon
- Metadata display
- Action menu
- Preview thumbnail
- Tags display
```

#### DocumentGrid
```tsx
interface DocumentGridProps {
  documents: Document[]
  columns?: 2 | 3 | 4 | 'auto'
  selectable?: boolean
  onSelect?: (docs: Document[]) => void
}

// Features:
- Responsive grid layout
- Lazy loading
- Selection mode
- Sorting options
- Filter toolbar
```

### 4. Analytics Components

#### MetricCard
```tsx
interface MetricCardProps {
  title: string
  value: number | string
  change?: {
    value: number
    trend: 'up' | 'down' | 'neutral'
  }
  icon?: IconType
  sparkline?: number[]
}

// Features:
- Animated number transitions
- Trend indicators
- Mini sparkline chart
- Click for details
- Loading skeleton
```

#### ChartContainer
```tsx
interface ChartContainerProps {
  title: string
  data: ChartData
  type: 'line' | 'bar' | 'pie' | 'area' | 'scatter'
  controls?: ChartControl[]
  exportable?: boolean
}

// Features:
- Interactive charts (Recharts)
- Zoom and pan
- Data point tooltips
- Export to PNG/SVG
- Responsive sizing
```

#### AnalyticsDashboard
```tsx
interface DashboardProps {
  widgets: Widget[]
  layout: 'fixed' | 'responsive' | 'custom'
  editable?: boolean
  onLayoutChange?: (layout: Layout) => void
}

// Features:
- Drag-and-drop widgets
- Customizable layout
- Widget library
- Save configurations
- Full-screen widgets
```

### 5. AI/Chat Components

#### ChatInterface
```tsx
interface ChatInterfaceProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  suggestions?: string[]
  typing?: boolean
  model?: AIModel
}

// Features:
- Message bubbles
- Typing indicators
- Suggested prompts
- File attachments
- Code highlighting
- Copy responses
```

#### AIAssistant
```tsx
interface AIAssistantProps {
  context?: Document[]
  capabilities: AICapability[]
  onAction: (action: AIAction) => void
}

// Features:
- Floating assistant widget
- Context awareness
- Quick actions menu
- Voice input
- Response streaming
```

### 6. Form Components

#### SmartForm
```tsx
interface SmartFormProps {
  schema: FormSchema
  values?: FormValues
  onSubmit: (values: FormValues) => void
  validation?: ValidationRules
}

// Features:
- Dynamic field generation
- Conditional fields
- Real-time validation
- Auto-save drafts
- Field dependencies
```

#### FilterPanel
```tsx
interface FilterPanelProps {
  filters: Filter[]
  values: FilterValues
  onChange: (values: FilterValues) => void
  presets?: FilterPreset[]
}

// Features:
- Collapsible sections
- Active filter badges
- Clear all option
- Save filter sets
- Applied count display
```

### 7. Data Display Components

#### DataTable
```tsx
interface DataTableProps {
  columns: Column[]
  data: any[]
  pagination?: PaginationConfig
  sorting?: SortingConfig
  selection?: SelectionConfig
}

// Features:
- Virtual scrolling
- Column resizing
- Sort indicators
- Row selection
- Cell editing
- Export functionality
```

#### Timeline
```tsx
interface TimelineProps {
  events: TimelineEvent[]
  orientation: 'vertical' | 'horizontal'
  grouped?: boolean
  interactive?: boolean
}

// Features:
- Event clustering
- Zoom controls
- Date filtering
- Event details popup
- Milestone markers
```

### 8. Feedback Components

#### NotificationToast
```tsx
interface NotificationProps {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  action?: NotificationAction
  duration?: number
}

// Features:
- Auto-dismiss
- Action buttons
- Stack management
- Progress indicator
- Persistence option
```

#### ProgressTracker
```tsx
interface ProgressTrackerProps {
  steps: Step[]
  current: number
  orientation?: 'horizontal' | 'vertical'
  showDetails?: boolean
}

// Features:
- Step indicators
- Progress bar
- Error states
- Clickable steps
- Time estimates
```

## Responsive Design

### Breakpoints
```css
- Mobile: 0-639px
- Tablet: 640-1023px
- Desktop: 1024-1439px
- Wide: 1440px+
```

### Mobile-First Approach
- Touch-friendly targets (44px minimum)
- Swipe gestures support
- Bottom sheet patterns
- Collapsible sections
- Progressive disclosure

## Accessibility Standards

### WCAG 2.1 AA Compliance
- Semantic HTML structure
- ARIA labels and roles
- Keyboard navigation
- Focus management
- Screen reader support
- High contrast mode
- Reduced motion support

### Keyboard Shortcuts
```
- Cmd/Ctrl + K: Quick search
- Cmd/Ctrl + /: Help menu
- Cmd/Ctrl + B: Toggle sidebar
- Cmd/Ctrl + D: Toggle dark mode
- Esc: Close modals/dropdowns
- Tab: Navigate forward
- Shift + Tab: Navigate backward
```

## Animation & Interactions

### Micro-interactions
- Button hover states
- Loading spinners
- Progress indicators
- Success checkmarks
- Error shakes
- Tooltip reveals

### Page Transitions
- Fade in/out: 200ms
- Slide: 300ms
- Modal backdrop: 150ms
- Accordion expand: 250ms
- Tab switch: 100ms

## Loading States

### Skeleton Screens
- Text placeholders
- Image placeholders
- Card skeletons
- Table row skeletons
- Chart placeholders

### Progressive Loading
- Above-the-fold priority
- Lazy load images
- Infinite scroll
- Virtual lists
- Code splitting

## Error States

### Error Boundaries
- Fallback UI components
- Error recovery options
- Support contact info
- Debug information (dev mode)

### Validation Feedback
- Inline field errors
- Form summary errors
- Success confirmations
- Warning messages
- Info tooltips

## Dark Mode Support

### Implementation
- CSS variables for colors
- System preference detection
- Manual toggle option
- Persistent user preference
- Smooth transitions

### Color Adjustments
- Inverted backgrounds
- Adjusted contrasts
- Dimmed highlights
- Modified shadows
- Adapted charts

## Performance Optimizations

### Component Optimization
- React.memo for pure components
- useMemo for expensive computations
- useCallback for stable references
- Virtual scrolling for long lists
- Debounced inputs

### Asset Optimization
- WebP images with fallbacks
- SVG icons sprite sheet
- Lazy loaded images
- Responsive images
- Font subsetting

## Component Documentation

### Storybook Integration
- Component playground
- Props documentation
- Usage examples
- Accessibility tests
- Visual regression tests

### Design Tokens
```json
{
  "colors": {...},
  "typography": {...},
  "spacing": {...},
  "shadows": {...},
  "animations": {...}
}
```

## Testing Strategy

### Component Testing
- Unit tests with Vitest
- Integration tests
- Visual regression tests
- Accessibility tests
- Performance tests

### User Testing
- A/B testing framework
- Analytics integration
- Heatmap tracking
- User feedback widgets
- Session recording
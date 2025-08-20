import { useState } from 'react';
import type { FilterState, RFP } from '../types/rfp';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Checkbox } from './ui/checkbox';
import { Calendar } from './ui/calendar';
import { 
  Search, 
  Filter, 
  X, 
  Calendar as CalendarIcon, 
  Building, 
  Tag, 
  Clock,
  TrendingUp,
  Sparkles
} from 'lucide-react';

interface FilterBarProps {
  rfps: RFP[];
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onClearFilters: () => void;
}

export function FilterBar({ rfps, filters, onFiltersChange, onClearFilters }: FilterBarProps) {
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Get unique values from RFPs for filter options
  const getUniqueValues = (field: string) => {
    const values = rfps
      .map(rfp => rfp.extracted_fields?.[field])
      .filter(Boolean)
      .filter((value, index, array) => array.indexOf(value) === index)
      .sort();
    return values;
  };

  const uniqueIssuers = getUniqueValues('issuer');
  const uniqueEventAssociations = getUniqueValues('event_association');
  const uniqueProcurementTypes = getUniqueValues('procurement_type');

  const hasActiveFilters = 
    filters.searchTerm ||
    filters.issuers.length > 0 ||
    filters.eventAssociations.length > 0 ||
    filters.procurementTypes.length > 0 ||
    filters.dateRange.start ||
    filters.dateRange.end ||
    filters.quickFilters.newThisWeek ||
    filters.quickFilters.closingSoon ||
    filters.quickFilters.highValue ||
    filters.showIgnored;

  const activeFilterCount = [
    filters.searchTerm ? 1 : 0,
    filters.issuers.length,
    filters.eventAssociations.length,
    filters.procurementTypes.length,
    filters.dateRange.start || filters.dateRange.end ? 1 : 0,
    Object.values(filters.quickFilters).filter(Boolean).length,
    filters.showIgnored ? 1 : 0
  ].reduce((sum, count) => sum + count, 0);

  const updateFilters = (updates: Partial<FilterState>) => {
    onFiltersChange({ ...filters, ...updates });
  };

  const toggleQuickFilter = (filterKey: keyof FilterState['quickFilters']) => {
    updateFilters({
      quickFilters: {
        ...filters.quickFilters,
        [filterKey]: !filters.quickFilters[filterKey]
      }
    });
  };

  const toggleArrayFilter = (array: string[], value: string, field: keyof FilterState) => {
    const newArray = array.includes(value)
      ? array.filter(item => item !== value)
      : [...array, value];
    
    updateFilters({ [field]: newArray });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center space-y-4 lg:space-y-0 lg:space-x-4">
        {/* Search Input */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search RFPs by title, description, or issuer..."
            value={filters.searchTerm}
            onChange={(e) => updateFilters({ searchTerm: e.target.value })}
            className="pl-10"
          />
        </div>

        {/* Quick Filters */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant={filters.quickFilters.newThisWeek ? 'default' : 'outline'}
            size="sm"
            onClick={() => toggleQuickFilter('newThisWeek')}
            className="flex items-center space-x-1"
          >
            <Sparkles className="w-4 h-4" />
            <span>New This Week</span>
          </Button>

          <Button
            variant={filters.quickFilters.closingSoon ? 'default' : 'outline'}
            size="sm"
            onClick={() => toggleQuickFilter('closingSoon')}
            className="flex items-center space-x-1"
          >
            <Clock className="w-4 h-4" />
            <span>Closing Soon</span>
          </Button>

          <Button
            variant={filters.quickFilters.highValue ? 'default' : 'outline'}
            size="sm"
            onClick={() => toggleQuickFilter('highValue')}
            className="flex items-center space-x-1"
          >
            <TrendingUp className="w-4 h-4" />
            <span>High Value ($1M+)</span>
          </Button>
        </div>

        {/* Advanced Filters Toggle */}
        <Popover open={isFilterOpen} onOpenChange={setIsFilterOpen}>
          <PopoverTrigger asChild>
            <Button 
              variant="outline" 
              className="flex items-center space-x-2"
            >
              <Filter className="w-4 h-4" />
              <span>Filters</span>
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-4" align="end">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">Advanced Filters</h3>
                {hasActiveFilters && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClearFilters}
                    className="text-red-600 hover:text-red-700"
                  >
                    Clear All
                  </Button>
                )}
              </div>

              {/* Issuers Filter */}
              {uniqueIssuers.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-700 flex items-center space-x-2 mb-2">
                    <Building className="w-4 h-4" />
                    <span>Issuers</span>
                  </label>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {uniqueIssuers.map((issuer) => (
                      <div key={issuer} className="flex items-center space-x-2">
                        <Checkbox
                          checked={filters.issuers.includes(issuer)}
                          onCheckedChange={() => 
                            toggleArrayFilter(filters.issuers, issuer, 'issuers')
                          }
                        />
                        <span className="text-sm">{issuer}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Event Associations Filter */}
              {uniqueEventAssociations.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-700 flex items-center space-x-2 mb-2">
                    <Tag className="w-4 h-4" />
                    <span>Event Associations</span>
                  </label>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {uniqueEventAssociations.map((association) => (
                      <div key={association} className="flex items-center space-x-2">
                        <Checkbox
                          checked={filters.eventAssociations.includes(association)}
                          onCheckedChange={() => 
                            toggleArrayFilter(filters.eventAssociations, association, 'eventAssociations')
                          }
                        />
                        <span className="text-sm">{association}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Procurement Types Filter */}
              {uniqueProcurementTypes.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-700 flex items-center space-x-2 mb-2">
                    <Tag className="w-4 h-4" />
                    <span>Procurement Types</span>
                  </label>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {uniqueProcurementTypes.map((type) => (
                      <div key={type} className="flex items-center space-x-2">
                        <Checkbox
                          checked={filters.procurementTypes.includes(type)}
                          onCheckedChange={() => 
                            toggleArrayFilter(filters.procurementTypes, type, 'procurementTypes')
                          }
                        />
                        <span className="text-sm">{type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Date Range Filter */}
              <div>
                <label className="text-sm font-medium text-gray-700 flex items-center space-x-2 mb-2">
                  <CalendarIcon className="w-4 h-4" />
                  <span>Posted Date Range</span>
                </label>
                <div className="space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="justify-start text-left font-normal"
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {filters.dateRange.start ? 
                            filters.dateRange.start.toLocaleDateString() : 
                            "Start date"
                          }
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={filters.dateRange.start}
                          onSelect={(date: Date | undefined) => updateFilters({
                            dateRange: { ...filters.dateRange, start: date }
                          })}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>

                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="justify-start text-left font-normal"
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {filters.dateRange.end ? 
                            filters.dateRange.end.toLocaleDateString() : 
                            "End date"
                          }
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={filters.dateRange.end}
                          onSelect={(date: Date | undefined) => updateFilters({
                            dateRange: { ...filters.dateRange, end: date }
                          })}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                  
                  {(filters.dateRange.start || filters.dateRange.end) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => updateFilters({ dateRange: {} })}
                      className="text-red-600 hover:text-red-700"
                    >
                      Clear Date Range
                    </Button>
                  )}
                </div>
              </div>

              {/* Show Ignored Toggle */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={filters.showIgnored}
                  onCheckedChange={(checked: boolean) => updateFilters({ showIgnored: !!checked })}
                />
                <span className="text-sm">Show ignored RFPs</span>
              </div>
            </div>
          </PopoverContent>
        </Popover>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="flex items-center space-x-1 text-gray-500 hover:text-red-600"
          >
            <X className="w-4 h-4" />
            <span>Clear</span>
          </Button>
        )}
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t">
          {filters.searchTerm && (
            <Badge variant="secondary" className="flex items-center space-x-1">
              <span>Search: "{filters.searchTerm}"</span>
              <X 
                className="w-3 h-3 cursor-pointer hover:text-red-600" 
                onClick={() => updateFilters({ searchTerm: '' })}
              />
            </Badge>
          )}
          
          {filters.issuers.map((issuer) => (
            <Badge key={issuer} variant="secondary" className="flex items-center space-x-1">
              <span>Issuer: {issuer}</span>
              <X 
                className="w-3 h-3 cursor-pointer hover:text-red-600" 
                onClick={() => toggleArrayFilter(filters.issuers, issuer, 'issuers')}
              />
            </Badge>
          ))}
          
          {filters.eventAssociations.map((association) => (
            <Badge key={association} variant="secondary" className="flex items-center space-x-1">
              <span>Event: {association}</span>
              <X 
                className="w-3 h-3 cursor-pointer hover:text-red-600" 
                onClick={() => toggleArrayFilter(filters.eventAssociations, association, 'eventAssociations')}
              />
            </Badge>
          ))}
          
          {filters.procurementTypes.map((type) => (
            <Badge key={type} variant="secondary" className="flex items-center space-x-1">
              <span>Type: {type}</span>
              <X 
                className="w-3 h-3 cursor-pointer hover:text-red-600" 
                onClick={() => toggleArrayFilter(filters.procurementTypes, type, 'procurementTypes')}
              />
            </Badge>
          ))}
          
          {(filters.dateRange.start || filters.dateRange.end) && (
            <Badge variant="secondary" className="flex items-center space-x-1">
              <span>
                Date: {filters.dateRange.start?.toLocaleDateString()} - {filters.dateRange.end?.toLocaleDateString()}
              </span>
              <X 
                className="w-3 h-3 cursor-pointer hover:text-red-600" 
                onClick={() => updateFilters({ dateRange: {} })}
              />
            </Badge>
          )}
        </div>
      )}
    </div>
  );
}

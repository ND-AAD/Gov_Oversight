import { useState } from 'react';
import { FilterState, RFP } from '../types/rfp';
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
import { getUniqueValues } from '../data/mockData';

interface FilterBarProps {
  rfps: RFP[];
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onClearFilters: () => void;
}

export function FilterBar({ rfps, filters, onFiltersChange, onClearFilters }: FilterBarProps) {
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isDateRangeOpen, setIsDateRangeOpen] = useState(false);

  const uniqueIssuers = getUniqueValues(rfps, 'issuer');
  const uniqueEventAssociations = getUniqueValues(rfps, 'event_association');
  const uniqueProcurementTypes = getUniqueValues(rfps, 'procurement_type');

  const handleSearchChange = (value: string) => {
    onFiltersChange({
      ...filters,
      searchTerm: value
    });
  };

  const handleMultiSelectChange = (
    field: 'issuers' | 'eventAssociations' | 'procurementTypes',
    value: string,
    checked: boolean
  ) => {
    const currentValues = filters[field];
    const newValues = checked
      ? [...currentValues, value]
      : currentValues.filter(v => v !== value);
    
    onFiltersChange({
      ...filters,
      [field]: newValues
    });
  };

  const handleQuickFilterChange = (
    field: 'newThisWeek' | 'closingSoon' | 'highValue',
    checked: boolean
  ) => {
    onFiltersChange({
      ...filters,
      quickFilters: {
        ...filters.quickFilters,
        [field]: checked
      }
    });
  };

  const handleDateRangeChange = (range: { start?: Date; end?: Date }) => {
    onFiltersChange({
      ...filters,
      dateRange: range
    });
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.searchTerm) count++;
    if (filters.issuers.length > 0) count++;
    if (filters.eventAssociations.length > 0) count++;
    if (filters.procurementTypes.length > 0) count++;
    if (filters.dateRange.start || filters.dateRange.end) count++;
    if (Object.values(filters.quickFilters).some(Boolean)) count++;
    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  return (
    <div className="sticky top-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b z-40">
      <div className="p-4">
        {/* Main Filter Bar - Compact single line on wide screens */}
        <div className="flex flex-col lg:flex-row gap-3 lg:gap-4">
          {/* Search Bar */}
          <div className="relative flex-1 min-w-0">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search RFPs by title, description, or issuer..."
              value={filters.searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Filter Controls */}
          <div className="flex flex-wrap gap-2 shrink-0">
            <Button
              variant={filters.quickFilters.newThisWeek ? "default" : "outline"}
              size="sm"
              onClick={() => handleQuickFilterChange('newThisWeek', !filters.quickFilters.newThisWeek)}
              className="flex items-center gap-1"
            >
              <Sparkles className="h-3 w-3" />
              New This Week
            </Button>
            
            <Button
              variant={filters.quickFilters.closingSoon ? "destructive" : "outline"}
              size="sm"
              onClick={() => handleQuickFilterChange('closingSoon', !filters.quickFilters.closingSoon)}
              className="flex items-center gap-1"
            >
              <Clock className="h-3 w-3" />
              Closing Soon
            </Button>
            
            <Button
              variant={filters.quickFilters.highValue ? "default" : "outline"}
              size="sm"
              onClick={() => handleQuickFilterChange('highValue', !filters.quickFilters.highValue)}
              className="flex items-center gap-1"
            >
              <TrendingUp className="h-3 w-3" />
              High Value ($1M+)
            </Button>

            {/* Advanced Filters Popover */}
            <Popover open={isFilterOpen} onOpenChange={setIsFilterOpen}>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="flex items-center gap-1">
                  <Filter className="h-3 w-3" />
                  More Filters
                  {activeFilterCount > 0 && (
                    <Badge variant="secondary" className="ml-1 h-4 w-4 p-0 flex items-center justify-center">
                      {activeFilterCount}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80 p-4" align="start">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">Advanced Filters</h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={onClearFilters}
                      disabled={activeFilterCount === 0}
                    >
                      Clear All
                    </Button>
                  </div>

                  {/* Issuer Filter */}
                  <div>
                    <label className="flex items-center gap-2 mb-2">
                      <Building className="h-4 w-4" />
                      Issuing Agency
                    </label>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {uniqueIssuers.map(issuer => (
                        <div key={issuer} className="flex items-center space-x-2">
                          <Checkbox
                            id={`issuer-${issuer}`}
                            checked={filters.issuers.includes(issuer)}
                            onCheckedChange={(checked) => 
                              handleMultiSelectChange('issuers', issuer, checked as boolean)
                            }
                          />
                          <label 
                            htmlFor={`issuer-${issuer}`} 
                            className="text-sm cursor-pointer"
                          >
                            {issuer}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Event Association Filter */}
                  <div>
                    <label className="flex items-center gap-2 mb-2">
                      <Tag className="h-4 w-4" />
                      Event Association
                    </label>
                    <div className="space-y-2">
                      {uniqueEventAssociations.map(association => (
                        <div key={association} className="flex items-center space-x-2">
                          <Checkbox
                            id={`event-${association}`}
                            checked={filters.eventAssociations.includes(association)}
                            onCheckedChange={(checked) => 
                              handleMultiSelectChange('eventAssociations', association, checked as boolean)
                            }
                          />
                          <label 
                            htmlFor={`event-${association}`} 
                            className="text-sm cursor-pointer"
                          >
                            {association}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Procurement Type Filter */}
                  <div>
                    <label className="flex items-center gap-2 mb-2">
                      <Tag className="h-4 w-4" />
                      Procurement Type
                    </label>
                    <div className="space-y-2">
                      {uniqueProcurementTypes.map(type => (
                        <div key={type} className="flex items-center space-x-2">
                          <Checkbox
                            id={`type-${type}`}
                            checked={filters.procurementTypes.includes(type)}
                            onCheckedChange={(checked) => 
                              handleMultiSelectChange('procurementTypes', type, checked as boolean)
                            }
                          />
                          <label 
                            htmlFor={`type-${type}`} 
                            className="text-sm cursor-pointer"
                          >
                            {type}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Date Range Filter */}
                  <div>
                    <label className="flex items-center gap-2 mb-2">
                      <CalendarIcon className="h-4 w-4" />
                      Posted Date Range
                    </label>
                    <Popover open={isDateRangeOpen} onOpenChange={setIsDateRangeOpen}>
                      <PopoverTrigger asChild>
                        <Button variant="outline" className="w-full justify-start">
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {filters.dateRange.start ? (
                            filters.dateRange.end ? (
                              `${filters.dateRange.start.toLocaleDateString()} - ${filters.dateRange.end.toLocaleDateString()}`
                            ) : (
                              `From ${filters.dateRange.start.toLocaleDateString()}`
                            )
                          ) : (
                            "Select date range"
                          )}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          initialFocus
                          mode="range"
                          defaultMonth={filters.dateRange.start}
                          selected={{
                            from: filters.dateRange.start,
                            to: filters.dateRange.end
                          }}
                          onSelect={(range) => {
                            handleDateRangeChange({
                              start: range?.from,
                              end: range?.to
                            });
                            if (range?.from && range?.to) {
                              setIsDateRangeOpen(false);
                            }
                          }}
                          numberOfMonths={2}
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            {/* Clear All Button */}
            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearFilters}
                className="flex items-center gap-1"
              >
                <X className="h-3 w-3" />
                Clear All ({activeFilterCount})
              </Button>
            )}
          </div>
        </div>

        {/* Active Filters Display */}
        {activeFilterCount > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {filters.searchTerm && (
              <Badge variant="secondary" className="flex items-center gap-1">
                Search: "{filters.searchTerm}"
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => handleSearchChange('')}
                />
              </Badge>
            )}
            
            {filters.issuers.map(issuer => (
              <Badge key={issuer} variant="secondary" className="flex items-center gap-1">
                {issuer}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => handleMultiSelectChange('issuers', issuer, false)}
                />
              </Badge>
            ))}
            
            {filters.eventAssociations.map(association => (
              <Badge key={association} variant="secondary" className="flex items-center gap-1">
                {association}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => handleMultiSelectChange('eventAssociations', association, false)}
                />
              </Badge>
            ))}
            
            {filters.procurementTypes.map(type => (
              <Badge key={type} variant="secondary" className="flex items-center gap-1">
                {type}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => handleMultiSelectChange('procurementTypes', type, false)}
                />
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}